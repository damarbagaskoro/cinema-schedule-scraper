import logging
from datetime import date, datetime

import requests
from bs4 import BeautifulSoup, Tag


def _extract_theater_name(page: BeautifulSoup) -> str | None:
    """Extracts the theater name."""
    tag = page.find("h1")
    return tag.text.strip() if tag else None


def _extract_film_info(card: Tag) -> tuple[str | None, str | None]:
    """
    Extracts title and primary genre from a film card.
    Strips duration from genre field.
    """
    title_tag = card.find("a")
    genre_tag = card.find("p")

    title = title_tag.text.strip() if title_tag else None
    if genre_tag:
        raw_genre = genre_tag.text.strip()
        genre_part = raw_genre.split(" - ")[0].strip()
        genre = genre_part.split(",")[0].strip()
    else:
        genre = None
    return title, genre


def _extract_studio_block(bar: Tag) -> tuple[str | None, str | None, list[str]]:
    """
    Extracts studio_type, ticket_price, and screening_times from a studio block.

    The `bar` argument can be:
    - The `full sched_desc` div, to handle the first listed studio_type
    - A `div.mtop10` element, to handle any extra studio_type
    """
    studio_type_tag = bar.find("span", class_="showgroup")
    studio_type = studio_type_tag.text.strip() if studio_type_tag else None

    ticket_price_tag = bar.find("span", class_="htm")
    if ticket_price_tag:
        ticket_price = (
            ticket_price_tag.text.strip()
            .replace("Tiket Rp ", "")
            .replace(".", "")
            .strip()
        )
    else:
        ticket_price = None

    screening_times_tag = bar.find("ul", class_="usch")
    screening_times = (
        [li.get_text(strip=True) for li in screening_times_tag.find_all("li")]
        if screening_times_tag
        else []
    )

    return studio_type, ticket_price, screening_times


def scrape_theater(
    response: requests.Response,
    today: date,
    ingested_at: datetime,
) -> list[dict]:
    """
    Parses a theater page and returns a list of screening records.
    Each record is one row: one film × one studio type × one screening time.
    """
    page = BeautifulSoup(response.text, "html.parser")
    records = []

    theater_name = _extract_theater_name(page)
    if not theater_name:
        logging.warning("Could not extract theater name. Skipping page.")
        return records

    title_cards = page.find_all("div", class_="col-sm-10 sched_desc")

    # --- Inactive theater ---
    if not title_cards:
        logging.info(f"No screenings found for '{theater_name}'. Marking as inactive.")
        records.append(
            {
                "date": today,
                "theater_name": theater_name,
                "title": None,
                "genre": None,
                "studio_type": None,
                "screening_time": None,
                "ticket_price": None,
                "theater_status": "inactive",
                "ingested_at": ingested_at,
                "source_url": response.url,
            }
        )
        return records

    # --- Active theater ---
    for card in title_cards:
        title, genre = _extract_film_info(card)
        if not title or not genre:
            logging.warning(
                f"Failed to parse title or genre in '{theater_name}' "
                f"(url: {response.url}) — raw text: {card.get_text(separator=' ', strip=True)[:120]}"
            )
            continue

        # --- Studio Type #1 ---
        studio_type, ticket_price, screening_times = _extract_studio_block(card)
        for screening_time in screening_times:
            records.append(
                {
                    "date": today,
                    "theater_name": theater_name,
                    "title": title,
                    "genre": genre,
                    "studio_type": studio_type,
                    "screening_time": screening_time,
                    "ticket_price": ticket_price,
                    "theater_status": "active",
                    "ingested_at": ingested_at,
                    "source_url": response.url,
                }
            )

        # --- Extra Studio Types ---
        for extra_studio in card.find_all("div", class_="mtop10"):
            studio_type, ticket_price, screening_times = _extract_studio_block(
                extra_studio
            )
            for screening_time in screening_times:
                records.append(
                    {
                        "date": today,
                        "theater_name": theater_name,
                        "title": title,
                        "genre": genre,
                        "studio_type": studio_type,
                        "screening_time": screening_time,
                        "ticket_price": ticket_price,
                        "theater_status": "active",
                        "ingested_at": ingested_at,
                        "source_url": response.url,
                    }
                )

    return records
