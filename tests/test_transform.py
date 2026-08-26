from datetime import date, datetime

import pytest

from pipeline.transform import clean_data


def make_row(**overrides):
    """Build a complete source row with optional field overrides."""
    row = {
        "tpep_pickup_datetime": datetime(2026, 5, 10, 9, 0),
        "tpep_dropoff_datetime": datetime(2026, 5, 10, 9, 30),
        "trip_distance": 4.0,
        "fare_amount": 20.0,
        "PULocationID": 10,
        "DOLocationID": 20,
    }
    row.update(overrides)
    return row


def test_clean_data_derives_trip_metrics_and_pickup_date(spark):
    result = clean_data(spark.createDataFrame([make_row()])).first()

    assert result.trip_duration == pytest.approx(30.0)
    assert result.revenue_per_mile == pytest.approx(5.0)
    assert result.pickup_date == date(2026, 5, 10)


def test_clean_data_drops_rows_with_required_nulls(spark):
    rows = [make_row(), make_row(DOLocationID=None)]

    result = clean_data(spark.createDataFrame(rows)).collect()

    assert len(result) == 1
    assert result[0].DOLocationID == 20
