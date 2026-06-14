import logging
import os
import sys
from datetime import date, datetime

import requests

from scraper.config import BASE_URL, HEADERS, MAX_FAILURE_RATE
from scraper.http_utilities import fetch_url, _polite_sleep
from scraper.url_collector import get_all_theater_urls
from scraper.parser import scrape_theater
from scraper.validator import validate_output

import pandas as pd


# ====================================
# LOGGING SETUP
# ====================================

os.makedirs("output", exist_ok=True)
os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("logs/scraper.log"), logging.StreamHandler()],
)


# ====================================
# LOG SUMMARY
# ====================================


def _log_summary(
    total: int, scraped: int, failed_count: int, failed_urls: list[str]
) -> None:
    """Logs the post-scrape run summary."""
    logging.info(f"Scraping complete. Total records: {total}")
    logging.info(f"Theaters scraped: {scraped}/{scraped + failed_count}")
    if failed_urls:
        logging.warning(f"Failed URLs ({failed_count}): {failed_urls}")
        failure_rate = failed_count / (scraped + failed_count)
        if failure_rate >= MAX_FAILURE_RATE:
            logging.warning(
                f"High failure rate detected ({failure_rate:.0%} of theaters could not be fetched). "
                f"This likely indicates a network or site-level problem, not isolated page errors. "
                f"Manually open the failed URLs in a browser to investigate."
            )


# ====================================
# MAIN PIPELINE
# ====================================


def run_scraper() -> bool:
    """
    Orchestrates the full scraping run: collect URLs, scrape, validate, save to CSV.
    Returns True on success, False on failure.
    """
    logging.info("=== Scraping started ===")
    today = date.today()
    ingested_at = datetime.now()
    all_records = []
    failed_urls = []

    session = requests.Session()
    session.headers.update(HEADERS)

    theater_urls = get_all_theater_urls(BASE_URL, session)
    if not theater_urls:
        logging.critical("No theater URLs collected. Cannot proceed.")
        return False

    for url in theater_urls:
        logging.info(f"Scraping: {url}")
        response = fetch_url(url, session)

        if not response:
            failed_urls.append(url)
            continue

        records = scrape_theater(response, today, ingested_at)
        all_records.extend(records)
        if len(records) == 0:
            logging.warning(
                f"Zero records extracted from {url}. Possible parsing issue."
            )
        else:
            logging.info(f"  >> {len(records)} records extracted.")

        _polite_sleep()

    # ── Log summary ──
    _log_summary(
        total=len(all_records),
        scraped=len(theater_urls) - len(failed_urls),
        failed_count=len(failed_urls),
        failed_urls=failed_urls,
    )

    if not all_records:
        logging.critical("No data was collected. CSV will not be saved.")
        return False

    # ── Build & Validate DataFrame ──
    df = pd.DataFrame(all_records)
    if not validate_output(df):
        logging.critical("Validation failed. Output will not be saved.")
        return False

    # ── Save to CSV ──
    filename = f"output/{today}_screening.csv"
    df.to_csv(filename, index=False)
    logging.info(f"Data saved to {filename} ({len(df)} rows).")
    logging.info("=== Scraping finished ===")
    return True


if __name__ == "__main__":
    success = run_scraper()
    sys.exit(0 if success else 1)
