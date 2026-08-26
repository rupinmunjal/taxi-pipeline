"""Clean and enrich taxi data with PySpark."""

import glob
import logging
import os
from datetime import date

from google.cloud import storage
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

from pipeline import config

config.setup_logging()
logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = [
    "tpep_pickup_datetime",
    "tpep_dropoff_datetime",
    "trip_distance",
    "fare_amount",
    "PULocationID",
    "DOLocationID",
]


def download_raw_from_gcs(bucket_name: str, prefix: str, local_dir: str) -> int:
    """Download all raw Parquet files from GCS to a local folder.

    Returns:
        The number of files downloaded.

    Raises:
        FileNotFoundError: If no Parquet files are found under the prefix.
    """
    os.makedirs(local_dir, exist_ok=True)
    client = storage.Client()
    bucket = client.bucket(bucket_name)

    downloaded = 0
    for blob in bucket.list_blobs(prefix=prefix):
        if blob.name.endswith(".parquet"):
            local_path = os.path.join(local_dir, os.path.basename(blob.name))
            blob.download_to_filename(local_path)
            logger.info("Downloaded %s -> %s", blob.name, local_path)
            downloaded += 1

    if downloaded == 0:
        raise FileNotFoundError(
            f"No .parquet files found under gs://{bucket_name}/{prefix}"
        )
    return downloaded


def upload_processed_to_gcs(bucket_name: str, local_dir: str, gcs_prefix: str) -> int:
    """Upload all processed partition files back to GCS.

    Returns:
        The number of files uploaded.
    """
    client = storage.Client()
    bucket = client.bucket(bucket_name)

    uploaded = 0
    for filepath in glob.glob(f"{local_dir}/**/*", recursive=True):
        if os.path.isfile(filepath):
            relative_path = os.path.relpath(filepath, local_dir)
            blob_path = f"{gcs_prefix}{relative_path}"
            bucket.blob(blob_path).upload_from_filename(filepath)
            uploaded += 1

    logger.info("Uploaded %d files to gs://%s/%s", uploaded, bucket_name, gcs_prefix)
    return uploaded


def clear_gcs_prefix(bucket_name: str, prefix: str) -> int:
    """Delete existing derived objects before publishing a replacement."""
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blobs = list(bucket.list_blobs(prefix=prefix))
    if blobs:
        bucket.delete_blobs(blobs)
    logger.info("Removed %d existing object(s) from gs://%s/%s", len(blobs), bucket_name, prefix)
    return len(blobs)


def get_spark_session() -> SparkSession:
    """Create (or fetch) the Spark session used for the transform stage."""
    return SparkSession.builder.appName("taxi-transform").getOrCreate()


def load_raw_data(spark: SparkSession, path: str) -> DataFrame:
    """Load raw Parquet files into a Spark DataFrame."""
    return spark.read.parquet(path)


def clean_data(
    df: DataFrame,
    expected_start: date | None = None,
    expected_end: date | None = None,
) -> DataFrame:
    """Remove invalid trips and add analytical columns."""
    pickup_time = F.unix_timestamp("tpep_pickup_datetime")
    dropoff_time = F.unix_timestamp("tpep_dropoff_datetime")

    cleaned = (
        df.dropna(subset=REQUIRED_COLUMNS)
        .filter(F.col("fare_amount") > 0)
        .filter(F.col("trip_distance") > 0)
        .filter(F.col("tpep_dropoff_datetime") > F.col("tpep_pickup_datetime"))
        .withColumn("trip_duration", (dropoff_time - pickup_time) / 60)
        .withColumn(
            "revenue_per_mile",
            F.col("fare_amount") / F.col("trip_distance"),
        )
        .withColumn("pickup_date", F.to_date("tpep_pickup_datetime"))
    )

    if expected_start is not None and expected_end is not None:
        cleaned = cleaned.filter(
            (F.col("pickup_date") >= F.lit(expected_start.isoformat()))
            & (F.col("pickup_date") < F.lit(expected_end.isoformat()))
        )
    return cleaned


def write_processed_data(df: DataFrame, path: str) -> None:
    """Write cleaned data partitioned by pickup date."""
    df.write.partitionBy("pickup_date").mode("overwrite").parquet(path)
    logger.info("Wrote processed data partitioned by pickup_date to %s", path)


def run() -> None:
    """Execute the full transform stage: download, clean, write, upload."""
    download_raw_from_gcs(
        config.GCS_BUCKET, config.GCS_RAW_PREFIX, config.LOCAL_RAW_DIR
    )

    spark = get_spark_session()
    try:
        df = load_raw_data(spark, f"{config.LOCAL_RAW_DIR}*.parquet")
        df_clean = clean_data(
            df,
            config.EXPECTED_PICKUP_START_DATE,
            config.EXPECTED_PICKUP_END_DATE,
        )
        write_processed_data(df_clean, config.LOCAL_PROCESSED_DIR)
        logger.info("Transform complete.")
    finally:
        spark.stop()

    clear_gcs_prefix(config.GCS_BUCKET, config.GCS_PROCESSED_PREFIX)
    upload_processed_to_gcs(
        config.GCS_BUCKET, config.LOCAL_PROCESSED_DIR, config.GCS_PROCESSED_PREFIX
    )


if __name__ == "__main__":
    run()
