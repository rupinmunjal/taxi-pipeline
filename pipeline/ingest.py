"""Upload local raw Parquet files to GCS."""

import glob
import logging
import os

from google.cloud import storage

from pipeline import config

config.setup_logging()
logger = logging.getLogger(__name__)


def upload_raw_to_gcs(bucket_name: str, local_dir: str, gcs_prefix: str) -> int:
    """Upload every local Parquet file in ``local_dir`` to GCS.

    Args:
        bucket_name: Destination GCS bucket name.
        local_dir: Local directory containing raw ``*.parquet`` files.
        gcs_prefix: Destination prefix (folder) within the bucket.

    Returns:
        The number of files uploaded.

    Raises:
        FileNotFoundError: If no Parquet files are found in ``local_dir``.
    """
    local_files = sorted(glob.glob(os.path.join(local_dir, "*.parquet")))
    if not local_files:
        raise FileNotFoundError(f"No .parquet files found under {local_dir!r}")

    client = storage.Client()
    bucket = client.bucket(bucket_name)

    uploaded = 0
    for local_path in local_files:
        blob_path = f"{gcs_prefix}{os.path.basename(local_path)}"
        bucket.blob(blob_path).upload_from_filename(local_path)
        logger.info("Uploaded %s -> gs://%s/%s", local_path, bucket_name, blob_path)
        uploaded += 1

    return uploaded


def run() -> None:
    """Run the ingestion stage using pipeline configuration."""
    logger.info("Starting ingestion: %s -> %s", config.LOCAL_RAW_DIR, config.GCS_RAW_URI)
    uploaded = upload_raw_to_gcs(
        config.GCS_BUCKET, config.LOCAL_RAW_DIR, config.GCS_RAW_PREFIX
    )
    logger.info(
        "Ingestion complete: %d file(s) uploaded to %s", uploaded, config.GCS_RAW_URI
    )


if __name__ == "__main__":
    run()
