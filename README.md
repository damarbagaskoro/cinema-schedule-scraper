# Indonesia's Daily Cinema Schedule Scraper

A simple city-level scraper for Indonesian cinema schedules, pulling daily showtimes from all theaters listed on jadwalnonton.com. Originally built as the ingestion layer of a larger pipeline, now reusable as a standalone scraper for any city on the site with minimal setup.

---

## Features

Collects film screening data across all listed cinemas in a configured city.

---

## Output

A daily `.csv` file named `YYYY-MM-DD_screening.csv` saved to the `output/` directory. Each row is one film × one studio type × one screening time combination.
 
| Column | Description |
|---|---|
| `date` | Scraping date |
| `theater_name` | Theater name |
| `title` | Film title |
| `genre` | Primary genre only — see Known Limitations |
| `studio_type` | Studio type (e.g. Regular 2D, IMAX, 2D Velvet) |
| `screening_time` | Showtime in `HH:MM` format |
| `ticket_price` | Ticket price in IDR, digits only (e.g. `45000`) |
| `theater_status` | `active` if screenings were found, `inactive` if none |
| `ingested_at` | Timestamp when the scraper ran |
| `source_url` | Theater page URL the record was parsed from |

---

## Project Structure

```
project-name/
│
├── scraper/
│   ├── __init__.py
│   ├── config.py          # All configuration: URL, exclusions, thresholds, request settings
│   ├── http_utilities.py  # fetch_url() and polite sleep between requests
│   ├── url_collector.py   # Theater URL discovery from paginated listing
│   ├── parser.py          # HTML parsing and record extraction
│   └── validator.py       # Output validation: schema, thresholds, data quality checks
│
├── output/                # CSV files land here (gitignored)
├── logs/                  # scraper.log lands here (gitignored)
│
├── main.py                # Entry point and pipeline orchestrator
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Quickstart
 
**1. Clone the repository**
```bash
git clone https://github.com/yourusername/cinema-schedule-scraper.git
cd cinema-schedule-scraper
```
 
**2. Install dependencies**
```bash
pip install -r requirements.txt
```
 
**3. Configure for your city**
 
Open `scraper/config.py` — it is the only file you need to touch. Update the following:
 
```python
# Replace with your city's URL from jadwalnonton.com
BASE_URL = "https://jadwalnonton.com/bioskop/di-bandung/"
 
# Add any cinema URLs you want to exclude from scraping
EXCLUDED_THEATERS = [
    "https://jadwalnonton.com/...",
]
```
 
To find your city's URL: visit [jadwalnonton.com](https://jadwalnonton.com), browse to your city's cinema listing, and copy the URL from your browser's address bar.
 
**4. Run**
```bash
python main.py
```
 
Output is saved to `output/YYYY-MM-DD_screening.csv`. Logs are written to `logs/scraper.log` and also printed to your terminal as the scraper runs.
 
> **Recommended run time: between 10:00 AM and 11:00 AM.** Some theaters remove past screenings from their page as the day progresses. Running before the first screenings start gives you the most complete daily snapshot.

---

## Configuration Reference
 
All configurable values live in `scraper/config.py`. You should not need to touch any other file for standard use.
 
| Variable | Default | Description |
|---|---|---|
| `BASE_URL` | Bandung city URL | Target city listing page |
| `EXCLUDED_THEATERS` | Empty list | Cinema URLs to skip during collection |
| `MIN_ACTIVE_RECORDS` | `0` | Pipeline stops if fewer active records are found — see Data Quality |
| `MAX_NULL_RATE` | `0.20` | Pipeline stops if critical fields exceed this null rate — see Data Quality |
| `MAX_FAILURE_RATE` | `0.50` | Logs a warning if this share of theater fetches fail |
| `REQUEST_TIMEOUT` | `10` | Seconds before a request gives up |
| `MAX_RETRIES` | `3` | Retry attempts per failed request |
| `RETRY_DELAY` | `5` | Base seconds between retries (multiplied per attempt) |
| `CRAWL_DELAY_MIN` | `1` | Minimum seconds between requests |
| `CRAWL_DELAY_MAX` | `3` | Maximum seconds between requests |

---

## Data Quality and Validation
 
The scraper validates its own output before saving. Understanding how it handles errors helps you interpret the logs correctly.
 
### What stops the pipeline (critical errors)
 
These conditions indicate a structural problem — either the site has changed its HTML layout, or something went fundamentally wrong with the run. The CSV will **not** be saved.
 
- **Schema failure:** the output is missing expected columns.
- **Too few active records:** fewer than `MIN_ACTIVE_RECORDS` active screening rows were found.
- **High null rate:** a critical field (`title`, `genre`, `studio_type`, `screening_time`) has more than `MAX_NULL_RATE` null values across active records.
You can tune `MIN_ACTIVE_RECORDS` and `MAX_NULL_RATE` in `config.py` to match your city's typical output volume.
 
### What gets logged as a warning (pipeline continues)
 
These are bad individual records, not structural failures. The CSV is still saved — it is up to you to decide how to handle flagged rows downstream.
 
- A small number of null values in critical fields (below the `MAX_NULL_RATE` threshold)
- Rows with non-numeric `ticket_price` values
- Rows with malformed `screening_time` values (not in `HH:MM` format)
- Duplicate rows
- Unexpected `theater_status` values
### What the scraper does not check
 
**Record volume is not validated.** The scraper does not compare today's output against previous runs. Day-to-day volume comparison (e.g. "today returned 30% fewer records than usual") is intentionally left to you — you know your city's typical schedule patterns better than the scraper does, and this kind of check is more meaningful when done across a history of runs rather than in isolation.

---

## Known Assumptions & Limitations

- **Source dependency:** The scraper is tightly coupled to jadwalnonton.com's HTML structure. If the site changes its layout, parsing will break and the output will degrade. This is detected indirectly through rising null rates or falling record counts. Silent parser failures where wrong-but-non-null data is extracted are a known blind spot.
- **Daily cadence:** This scraper is designed to run once per day. Running it multiple times on the same day will overwrite the existing CSV for that date. There is no duplicate-run protection.
- **Genre:** Only the first listed genre per film is stored. If a film is listed as `Animation, Adventure, Comedy`, only `Animation` is recorded.
- **Inactive theaters:** Theaters with no screenings today are recorded as a single row with `theater_status = inactive` and all film fields set to null. They are excluded from data quality threshold checks.
---

## Context: Where This Scraper Fits in the Larger Pipeline

As mentioned above, this scraper is originally designed as part of an ingestion layer for a larger film screening intelligence system. The full pipeline is:

```
[This repo] Scraper → Raw Landing Zone → Database → Dashboard
```

Feel free to reach out if you want to know more about the pipeline!

---

## License

MIT
