"""Load Hive-partitioned Parquet data from GCS into BigQuery."""

import logging

from google.cloud import bigquery

from pipeline import config

config.setup_logging()
logger = logging.getLogger(__name__)


def build_load_job_config(source_uri_prefix: str) -> bigquery.LoadJobConfig:
    """Build the configuration for a partition-aware Parquet load."""
    hive_partitioning = bigquery.HivePartitioningOptions()
    hive_partitioning.mode = "AUTO"
    hive_partitioning.source_uri_prefix = source_uri_prefix

    return bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.PARQUET,
        hive_partitioning=hive_partitioning,
        time_partitioning=bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            field="pickup_date",
        ),
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )


def load_parquet_to_bq(table_id: str, source_uri: str, source_uri_prefix: str) -> None:
    """Load Hive-partitioned Parquet files into a BigQuery table."""
    client = bigquery.Client()
    job_config = build_load_job_config(source_uri_prefix)

    logger.info("Starting BigQuery load job: %s -> %s", source_uri, table_id)
    load_job = client.load_table_from_uri(source_uri, table_id, job_config=job_config)
    load_job.result()

    row_count = client.get_table(table_id).num_rows
    logger.info("Loaded %d row(s) into %s", row_count, table_id)


def run() -> None:
    """Execute the load stage using pipeline configuration."""
    load_parquet_to_bq(
        config.BQ_TABLE_ID,
        config.GCS_PROCESSED_SOURCE_URI,
        config.GCS_PROCESSED_URI,
    )


if __name__ == "__main__":
    run()
