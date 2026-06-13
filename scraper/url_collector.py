import logging

import requests
from bs4 import BeautifulSoup

from scraper.config import EXCLUDED_THEATERS
from scraper.http_utilities import fetch_url, _polite_sleep


def _get_page_numbers(base_page: BeautifulSoup) -> list[int]:
    """
    Returns all page numbers from the pagination block.
    Defaults to [1] if single-page.
    """
    pagination = base_page.find("div", class_="paggingcont")
    if not pagination or not pagination.find("a"):
        logging.info("Single-page listing detected. Defaulting to page 1.")
        return [1]
    return [int(a.text) for a in pagination.find_all("a") if a.text.isdigit()]


def _get_theater_urls_from_page(page_html: str) -> list[str]:
    """Extracts all theater URLs from a single listing page."""
    soup = BeautifulSoup(page_html, "lxml")
    theater_cards = soup.find_all("div", class_="bg relative")
    return [card.a["href"] for card in theater_cards if card.a and card.a.get("href")]


def get_all_theater_urls(base_url: str, session: requests.Session) -> list[str]:
    """
    Collects all theater URLs across paginated listing pages,
    excluding EXCLUDED_THEATERS.
    """
    response = fetch_url(base_url, session)
    if not response:
        logging.error("Failed to fetch the base URL. Cannot collect theater URLs.")
        return []

    base_page = BeautifulSoup(response.text, "lxml")
    page_numbers = _get_page_numbers(base_page)
    all_urls = _get_theater_urls_from_page(response.text)

    for page in range(2, max(page_numbers) + 1):
        page_url = f"{base_url}?page={page}"
        logging.info(f"Collecting theater URLs from page {page}...")

        page_response = fetch_url(page_url, session)
        if not page_response:
            logging.warning(f"Skipping page {page} — failed to fetch.")
            continue

        all_urls.extend(_get_theater_urls_from_page(page_response.text))
        _polite_sleep()

    filtered_urls = [url for url in all_urls if url not in EXCLUDED_THEATERS]
    logging.info(f"Collected {len(filtered_urls)} theater URLs after exclusions.")
    return filtered_urls
