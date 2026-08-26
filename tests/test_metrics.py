import json

from pipeline import metrics


def sample_metrics():
    """Build stable metrics for formatter tests."""
    return metrics.PipelineMetrics(
        raw_rows=100,
        loaded_rows=95,
        rejected_rows=5,
        rejection_percent=5.0,
        retention_percent=95.0,
        raw_local_files=1,
        raw_local_bytes=1_000,
        gcs_raw_objects=1,
        gcs_raw_bytes=1_000,
        gcs_processed_objects=31,
        gcs_processed_bytes=2_000,
        bigquery_bytes=3_000,
        partition_count=31,
        min_pickup_date="2026-05-01",
        max_pickup_date="2026-05-31",
        derived_nulls=0,
        nonpositive_durations=0,
        outside_expected_window=0,
        unfiltered_scan_bytes=10_000,
        filtered_scan_bytes=100,
        scan_reduction_percent=99.0,
    )


def test_format_metrics_reports_core_values():
    output = metrics.format_metrics(sample_metrics())

    assert "Loaded rows: 95" in output
    assert "Rejected rows: 5 (5.00%)" in output
    assert "Partitions: 31 (2026-05-01 to 2026-05-31)" in output
    assert "99.00000% reduction" in output


def test_main_emits_json(monkeypatch, capsys):
    monkeypatch.setattr(metrics, "collect_metrics", sample_metrics)

    assert metrics.main(["--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["loaded_rows"] == 95
    assert payload["partition_count"] == 31
