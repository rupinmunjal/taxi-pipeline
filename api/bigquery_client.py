"""BigQuery configuration and the shared client instance."""

import os
from functools import lru_cache

from dotenv import load_dotenv
from google.cloud import bigquery

load_dotenv()


def _required_env(name: str) -> str:
    """Return a required environment variable."""
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


BQ_PROJECT = _required_env("BQ_PROJECT")
BQ_DATASET = _required_env("BQ_DATASET")
BQ_TABLE = os.getenv("BQ_TABLE", "trips")
BQ_TABLE_ID = f"{BQ_PROJECT}.{BQ_DATASET}.{BQ_TABLE}"


@lru_cache(maxsize=1)
def get_bigquery_client() -> bigquery.Client:
    """Create one shared BigQuery client for the API process."""
    return bigquery.Client(project=BQ_PROJECT)
