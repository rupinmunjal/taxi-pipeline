"""Verify the loaded BigQuery table and its partition pruning."""

import logging
import sys
from collections.abc import Callable
from dataclasses import dataclass

from google.cloud import bigquery

from pipeline import config

config.setup_logging()
logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = ("pickup_date", "trip_duration", "revenue_per_mile")


@dataclass(frozen=True)
class CheckResult:
    """Result of one pipeline verification check."""

    name: str
    passed: bool
    detail: str


def check_row_count(client: bigquery.Client, table_id: str) -> CheckResult:
    """Confirm that the destination table contains rows."""
    query = f"SELECT COUNT(*) AS row_count FROM `{table_id}`"
    row_count = next(iter(client.query(query).result()))["row_count"]
    passed = row_count > 0
    detail = (
        f"{row_count:,} row(s) in {table_id}"
        if passed
        else f"Table {table_id} contains 0 rows"
    )
    return CheckResult("Row count", passed, detail)


def check_schema_and_nulls(client: bigquery.Client, table_id: str) -> CheckResult:
    """Confirm derived columns exist and report their null counts."""
    schema_fields = {field.name for field in client.get_table(table_id).schema}
    missing = [column for column in REQUIRED_COLUMNS if column not in schema_fields]
    if missing:
        return CheckResult(
            "Schema and nulls",
            False,
            f"Missing expected column(s): {', '.join(missing)}",
        )

    expressions = ", ".join(
        f"COUNTIF({column} IS NULL) AS {column}_nulls"
        for column in REQUIRED_COLUMNS
    )
    row = next(iter(client.query(f"SELECT {expressions} FROM `{table_id}`").result()))
    summary = ", ".join(
        f"{column}={row[f'{column}_nulls']}" for column in REQUIRED_COLUMNS
    )
    return CheckResult("Schema and nulls", True, f"Null counts: {summary}")


def dry_run_bytes(client: bigquery.Client, query: str) -> int:
    """Return estimated bytes processed without executing a query."""
    job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
    return client.query(query, job_config=job_config).total_bytes_processed or 0


def get_sample_partition_date(client: bigquery.Client, table_id: str) -> str:
    """Return one populated pickup-date partition."""
    query = (
        f"SELECT MIN(pickup_date) AS pickup_date FROM `{table_id}` "
        "WHERE pickup_date IS NOT NULL"
    )
    pickup_date = next(iter(client.query(query).result()))["pickup_date"]
    if pickup_date is None:
        raise ValueError(f"No non-null pickup_date values found in {table_id}")
    return str(pickup_date)


def check_partition_pruning(client: bigquery.Client, table_id: str) -> CheckResult:
    """Confirm a pickup-date filter reduces estimated bytes processed."""
    sample_date = get_sample_partition_date(client, table_id)
    base_query = f"SELECT SUM(fare_amount) FROM `{table_id}`"
    filtered_query = f"{base_query} WHERE pickup_date = '{sample_date}'"
    unfiltered_bytes = dry_run_bytes(client, base_query)
    filtered_bytes = dry_run_bytes(client, filtered_query)
    detail = (
        f"unfiltered={unfiltered_bytes:,} bytes, "
        f"pickup_date={sample_date}={filtered_bytes:,} bytes"
    )
    return CheckResult(
        "Partition pruning",
        filtered_bytes < unfiltered_bytes,
        detail,
    )


Check = Callable[[bigquery.Client, str], CheckResult]
CHECKS: tuple[Check, ...] = (
    check_row_count,
    check_schema_and_nulls,
    check_partition_pruning,
)


def print_summary(results: list[CheckResult]) -> None:
    """Print an aligned verification summary."""
    name_width = max(len(result.name) for result in results)
    header = f"{'Check':<{name_width}}  {'Status':<6}  Detail"
    print(header)
    print("-" * len(header))
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(f"{result.name:<{name_width}}  {status:<6}  {result.detail}")


def run() -> int:
    """Run every verification check and return a process exit code."""
    client = bigquery.Client()
    results = []

    for check in CHECKS:
        try:
            result = check(client, config.BQ_TABLE_ID)
        except Exception as exc:
            logger.exception("Verification check failed: %s", check.__name__)
            result = CheckResult(check.__name__, False, str(exc))
        results.append(result)

    print_summary(results)
    return 0 if all(result.passed for result in results) else 1


if __name__ == "__main__":
    sys.exit(run())
