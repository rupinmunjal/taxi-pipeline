from datetime import date
from types import SimpleNamespace
from unittest.mock import Mock

from pipeline import verify


def query_result(row):
    """Create a BigQuery query-job mock yielding one row."""
    job = Mock()
    job.result.return_value = [row]
    return job


def test_row_count_fails_for_empty_table():
    client = Mock()
    client.query.return_value = query_result({"row_count": 0})

    result = verify.check_row_count(client, "project.dataset.trips")

    assert result.passed is False
    assert "0 rows" in result.detail


def test_schema_check_reports_missing_columns():
    client = Mock()
    client.get_table.return_value.schema = [SimpleNamespace(name="pickup_date")]

    result = verify.check_schema_and_nulls(client, "project.dataset.trips")

    assert result.passed is False
    assert "trip_duration" in result.detail
    assert "revenue_per_mile" in result.detail
    client.query.assert_not_called()


def test_partition_pruning_passes_when_filtered_scan_is_smaller(monkeypatch):
    client = Mock()
    monkeypatch.setattr(
        verify,
        "get_sample_partition_date",
        Mock(return_value=str(date(2026, 5, 1))),
    )
    monkeypatch.setattr(verify, "dry_run_bytes", Mock(side_effect=[1_000, 100]))

    result = verify.check_partition_pruning(client, "project.dataset.trips")

    assert result.passed is True
    assert "unfiltered=1,000 bytes" in result.detail
