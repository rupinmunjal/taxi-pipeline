import os

import pytest
from pyspark.sql import SparkSession

os.environ.setdefault("GCS_BUCKET", "test-bucket")
os.environ.setdefault("BQ_PROJECT", "test-project")
os.environ.setdefault("BQ_DATASET", "test_dataset")


@pytest.fixture(scope="session")
def spark():
    """Provide one local Spark session for transform unit tests."""
    session = (
        SparkSession.builder.master("local[1]")
        .appName("taxi-pipeline-tests")
        .config("spark.ui.enabled", "false")
        .getOrCreate()
    )
    yield session
    session.stop()
