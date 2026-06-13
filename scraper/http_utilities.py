import logging
import time
import random
import requests

from scraper.config import (
    MAX_RETRIES,
    REQUEST_TIMEOUT,
    RETRY_DELAY,
    CRAWL_DELAY_MIN,
    CRAWL_DELAY_MAX,
)


def fetch_url(url: str, session: requests.Session) -> requests.Response | None:
    """
    Fetches a URL.
    Returns a Response object on success, or None on failure.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = session.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logging.warning(f"Attempt {attempt}/{MAX_RETRIES} failed for {url}: {e}")
            if attempt < MAX_RETRIES:
                wait = RETRY_DELAY * attempt  # linear backoff
                logging.info(f"Retrying in {wait}s...")
                time.sleep(wait)

    logging.error(f"All {MAX_RETRIES} attempts failed for {url}. Skipping.")
    return None


def _polite_sleep() -> None:
    """Waits a random amount of time between requests to avoid hammering the server."""
    time.sleep(random.uniform(CRAWL_DELAY_MIN, CRAWL_DELAY_MAX))
