"""Collect reproducible local, GCS, and BigQuery pipeline metrics."""

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import pyarrow.parquet as parquet
from google.cloud import bigquery, storage

from pipeline import config
from pipeline.verify import dry_run_bytes, get_sample_partition_date


@dataclass(frozen=True)
class PipelineMetrics:
    """Measured pipeline volume, quality, storage, and pruning metrics."""

    raw_rows: int
    loaded_rows: int
    rejected_rows: int
    rejection_percent: float
    retention_percent: float
    raw_local_files: int
    raw_local_bytes: int
    gcs_raw_objects: int
    gcs_raw_bytes: int
    gcs_processed_objects: int
    gcs_processed_bytes: int
    bigquery_bytes: int
    partition_count: int
    min_pickup_date: str
    max_pickup_date: str
    derived_nulls: int
    nonpositive_durations: int
    outside_expected_window: int | None
    unfiltered_scan_bytes: int
    filtered_scan_bytes: int
    scan_reduction_percent: float


def local_parquet_stats(local_dir: str) -> tuple[int, int, int]:
    """Return local Parquet file count, rows, and bytes."""
    files = sorted(Path(local_dir).glob("*.parquet"))
    if not files:
        raise FileNotFoundError(f"No local Parquet files found in {local_dir!r}")
    rows = sum(parquet.ParquetFile(path).metadata.num_rows for path in files)
    return len(files), rows, sum(path.stat().st_size for path in files)


def gcs_prefix_stats(bucket: storage.Bucket, prefix: str) -> tuple[int, int]:
    """Return object count and total bytes for a GCS prefix."""
    blobs = list(bucket.list_blobs(prefix=prefix))
    return len(blobs), sum(blob.size or 0 for blob in blobs)


def collect_metrics() -> PipelineMetrics:
    """Collect metrics from local Parquet, GCS, and BigQuery."""
    raw_local_files, raw_rows, raw_local_bytes = local_parquet_stats(
        config.LOCAL_RAW_DIR
    )

    bucket = storage.Client().bucket(config.GCS_BUCKET)
    gcs_raw_objects, gcs_raw_bytes = gcs_prefix_stats(bucket, config.GCS_RAW_PREFIX)
    processed_objects, processed_bytes = gcs_prefix_stats(
        bucket, config.GCS_PROCESSED_PREFIX
    )

    client = bigquery.Client()
    table = client.get_table(config.BQ_TABLE_ID)
    window_expression = "NULL"
    if config.EXPECTED_PICKUP_START_DATE and config.EXPECTED_PICKUP_END_DATE:
        window_expression = (
            "COUNTIF(pickup_date < "
            f"DATE '{config.EXPECTED_PICKUP_START_DATE.isoformat()}' "
            "OR pickup_date >= "
            f"DATE '{config.EXPECTED_PICKUP_END_DATE.isoformat()}')"
        )

    query = f"""
        SELECT
          COUNT(DISTINCT pickup_date) AS partition_count,
          MIN(pickup_date) AS min_pickup_date,
          MAX(pickup_date) AS max_pickup_date,
          COUNTIF(
            pickup_date IS NULL
            OR trip_duration IS NULL
            OR revenue_per_mile IS NULL
          ) AS derived_nulls,
          COUNTIF(trip_duration <= 0) AS nonpositive_durations,
          {window_expression} AS outside_expected_window
        FROM `{config.BQ_TABLE_ID}`
    """
    quality = next(iter(client.query(query).result()))

    sample_date = get_sample_partition_date(client, config.BQ_TABLE_ID)
    unfiltered_query = f"SELECT SUM(fare_amount) FROM `{config.BQ_TABLE_ID}`"
    filtered_query = (
        f"{unfiltered_query} WHERE pickup_date = DATE '{sample_date}'"
    )
    unfiltered_bytes = dry_run_bytes(client, unfiltered_query)
    filtered_bytes = dry_run_bytes(client, filtered_query)
    rejected_rows = raw_rows - table.num_rows
    scan_reduction = (
        (unfiltered_bytes - filtered_bytes) / unfiltered_bytes * 100
        if unfiltered_bytes
        else 0.0
    )

    return PipelineMetrics(
        raw_rows=raw_rows,
        loaded_rows=table.num_rows,
        rejected_rows=rejected_rows,
        rejection_percent=rejected_rows / raw_rows * 100,
        retention_percent=table.num_rows / raw_rows * 100,
        raw_local_files=raw_local_files,
        raw_local_bytes=raw_local_bytes,
        gcs_raw_objects=gcs_raw_objects,
        gcs_raw_bytes=gcs_raw_bytes,
        gcs_processed_objects=processed_objects,
        gcs_processed_bytes=processed_bytes,
        bigquery_bytes=table.num_bytes,
        partition_count=quality["partition_count"],
        min_pickup_date=str(quality["min_pickup_date"]),
        max_pickup_date=str(quality["max_pickup_date"]),
        derived_nulls=quality["derived_nulls"],
        nonpositive_durations=quality["nonpositive_durations"],
        outside_expected_window=quality["outside_expected_window"],
        unfiltered_scan_bytes=unfiltered_bytes,
        filtered_scan_bytes=filtered_bytes,
        scan_reduction_percent=scan_reduction,
    )


def format_metrics(metrics: PipelineMetrics) -> str:
    """Format metrics for terminal and README use."""
    window_anomalies = (
        "not configured"
        if metrics.outside_expected_window is None
        else f"{metrics.outside_expected_window:,}"
    )
    return "\n".join(
        (
            f"Raw rows: {metrics.raw_rows:,}",
            f"Loaded rows: {metrics.loaded_rows:,}",
            f"Rejected rows: {metrics.rejected_rows:,} "
            f"({metrics.rejection_percent:.2f}%)",
            f"Retention: {metrics.retention_percent:.2f}%",
            f"Partitions: {metrics.partition_count:,} "
            f"({metrics.min_pickup_date} to {metrics.max_pickup_date})",
            f"Derived-field null rows: {metrics.derived_nulls:,}",
            f"Non-positive durations: {metrics.nonpositive_durations:,}",
            f"Rows outside expected window: {window_anomalies}",
            f"GCS raw: {metrics.gcs_raw_objects:,} objects, "
            f"{metrics.gcs_raw_bytes:,} bytes",
            f"GCS processed: {metrics.gcs_processed_objects:,} objects, "
            f"{metrics.gcs_processed_bytes:,} bytes",
            f"BigQuery logical bytes: {metrics.bigquery_bytes:,}",
            f"Partition scan: {metrics.unfiltered_scan_bytes:,} to "
            f"{metrics.filtered_scan_bytes:,} bytes "
            f"({metrics.scan_reduction_percent:.5f}% reduction)",
        )
    )


def main(argv: list[str] | None = None) -> int:
    """Print live metrics as text or JSON."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    args = parser.parse_args(argv)
    metrics = collect_metrics()
    print(json.dumps(asdict(metrics), indent=2) if args.json else format_metrics(metrics))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
