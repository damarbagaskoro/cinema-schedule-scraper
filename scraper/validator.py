import logging
from datetime import date

import pandas as pd

from scraper.config import MIN_ACTIVE_RECORDS, MAX_NULL_RATE


def _check_schema(df: pd.DataFrame) -> bool:
    """Checks that all expected columns are present."""
    expected_columns = {
        "date",
        "theater_name",
        "title",
        "genre",
        "studio_type",
        "screening_time",
        "ticket_price",
        "theater_status",
        "ingested_at",
        "source_url",
    }
    missing_cols = expected_columns - set(df.columns)
    if missing_cols:
        logging.critical(f"Output is missing expected columns: {missing_cols}")
        return False
    return True


def _check_thresholds(active_df: pd.DataFrame) -> bool:
    """
    Checks pipeline-killing thresholds.
    Returns False if the output is structurally untrustworthy.
    """
    passed = True

    if len(active_df) < MIN_ACTIVE_RECORDS:
        logging.critical(
            f"Only {len(active_df)} active records found. "
            f"Expected at least {MIN_ACTIVE_RECORDS}. Possible site structure change."
        )
        passed = False

    critical_fields = ["title", "screening_time", "genre", "studio_type"]
    for col in critical_fields:
        null_rate = active_df[col].isnull().mean()
        if null_rate > MAX_NULL_RATE:
            logging.critical(
                f"Column '{col}' has {null_rate:.0%} null rate in active records. "
                f"Possible parser drift."
            )
            passed = False

    return passed


def _check_completeness(df: pd.DataFrame, active_df: pd.DataFrame) -> None:
    """Checks for unexpected nulls and logs warnings."""
    for col in ["theater_name", "theater_status"]:
        null_count = df[col].isnull().sum()
        if null_count > 0:
            logging.warning(f"Column '{col}' has {null_count} null values.")

    critical_fields = ["title", "screening_time", "genre", "studio_type"]
    for col in critical_fields:
        null_rate = active_df[col].isnull().mean()
        if 0 < null_rate <= MAX_NULL_RATE:
            null_count = active_df[col].isnull().sum()
            logging.warning(
                f"Column '{col}' has {null_count} null values in active theater records."
            )


def _check_validity(df: pd.DataFrame, active_df: pd.DataFrame) -> None:
    """Checks value formats and category correctness, logs warnings."""
    duplicate_count = df.duplicated(
        subset=["date", "theater_name", "title", "studio_type", "screening_time"]
    ).sum()
    if duplicate_count > 0:
        logging.warning(f"Found {duplicate_count} duplicate rows in output.")

    invalid_prices = active_df[
        active_df["ticket_price"].notna()
        & ~active_df["ticket_price"].str.match(r"^\d+$", na=False)
    ]
    if not invalid_prices.empty:
        logging.warning(
            f"Found {len(invalid_prices)} rows with non-numeric ticket_price."
        )

    invalid_times = active_df[
        ~active_df["screening_time"].str.match(r"^\d{2}:\d{2}$", na=False)
    ]
    if not invalid_times.empty:
        logging.warning(
            f"Found {len(invalid_times)} rows with invalid screening_time format."
        )

    unexpected_dates = df[df["date"] != date.today()]
    if not unexpected_dates.empty:
        logging.warning(
            f"Found {len(unexpected_dates)} rows with unexpected date values."
        )

    invalid_status = df[~df["theater_status"].isin(["active", "inactive"])]
    if not invalid_status.empty:
        logging.warning(
            f"Found {len(invalid_status)} rows with unexpected theater_status values."
        )


def validate_output(df: pd.DataFrame) -> bool:
    """
    Runs data quality checks on the scraped DataFrame.
    Returns False on critical failures, logs warnings for bad records.
    """
    if not _check_schema(df):
        return False

    active_df = df[df["theater_status"] == "active"]

    passed = _check_thresholds(active_df)
    _check_completeness(df, active_df)
    _check_validity(df, active_df)

    return passed
