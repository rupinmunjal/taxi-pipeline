"""Centralized environment-based configuration for the taxi pipeline."""

import logging
import os
from datetime import date

from dotenv import load_dotenv

load_dotenv()


def setup_logging(level: int = logging.INFO) -> None:
    """Configure structured logging. Safe to call multiple times."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def _require_env(name: str) -> str:
    """Fetch a required environment variable or raise ``ValueError``."""
    value = os.getenv(name)
    if not value:
        raise ValueError(
            f"Missing required environment variable '{name}'. "
            "Set it in your shell or in a .env file at the project root."
        )
    return value


def parse_pickup_date_window(
    start_value: str | None,
    end_value: str | None,
) -> tuple[date | None, date | None]:
    """Parse an optional inclusive-start, exclusive-end pickup window."""
    if bool(start_value) != bool(end_value):
        raise ValueError(
            "EXPECTED_PICKUP_START_DATE and EXPECTED_PICKUP_END_DATE "
            "must be set together."
        )
    if not start_value:
        return None, None

    try:
        start = date.fromisoformat(start_value)
        end = date.fromisoformat(end_value)
    except ValueError as exc:
        raise ValueError("Expected pickup dates must use YYYY-MM-DD format.") from exc

    if end <= start:
        raise ValueError("EXPECTED_PICKUP_END_DATE must be later than the start date.")
    return start, end


GCS_BUCKET = _require_env("GCS_BUCKET")
BQ_PROJECT = _require_env("BQ_PROJECT")
BQ_DATASET = _require_env("BQ_DATASET")

BQ_TABLE = os.getenv("BQ_TABLE", "trips")
GCS_RAW_PREFIX = os.getenv("GCS_RAW_PREFIX", "raw/")
GCS_PROCESSED_PREFIX = os.getenv("GCS_PROCESSED_PREFIX", "processed/")
LOCAL_RAW_DIR = os.getenv("LOCAL_RAW_DIR", "data/raw/")
LOCAL_PROCESSED_DIR = os.getenv("LOCAL_PROCESSED_DIR", "data/processed/")
EXPECTED_PICKUP_START_DATE, EXPECTED_PICKUP_END_DATE = parse_pickup_date_window(
    os.getenv("EXPECTED_PICKUP_START_DATE"),
    os.getenv("EXPECTED_PICKUP_END_DATE"),
)

BQ_TABLE_ID = f"{BQ_PROJECT}.{BQ_DATASET}.{BQ_TABLE}"
GCS_RAW_URI = f"gs://{GCS_BUCKET}/{GCS_RAW_PREFIX}"
GCS_PROCESSED_URI = f"gs://{GCS_BUCKET}/{GCS_PROCESSED_PREFIX}"
GCS_PROCESSED_SOURCE_URI = f"{GCS_PROCESSED_URI}*.parquet"
