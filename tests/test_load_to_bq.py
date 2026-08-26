from unittest.mock import Mock

from google.cloud import bigquery

from pipeline import load_to_bq


def test_build_load_job_config_uses_hive_and_daily_time_partitioning():
    job_config = load_to_bq.build_load_job_config("gs://bucket/processed/")

    assert job_config.source_format == bigquery.SourceFormat.PARQUET
    assert job_config.write_disposition == bigquery.WriteDisposition.WRITE_TRUNCATE
    assert job_config.hive_partitioning.mode == "AUTO"
    assert job_config.hive_partitioning.source_uri_prefix == "gs://bucket/processed/"
    assert job_config.time_partitioning.field == "pickup_date"
    assert job_config.time_partitioning.type_ == bigquery.TimePartitioningType.DAY


def test_load_uses_bigquery_client_without_calling_gcp(monkeypatch):
    client = Mock()
    client.load_table_from_uri.return_value.result.return_value = None
    client.get_table.return_value.num_rows = 12
    monkeypatch.setattr(load_to_bq.bigquery, "Client", Mock(return_value=client))

    load_to_bq.load_parquet_to_bq(
        "project.dataset.trips",
        "gs://bucket/processed/*.parquet",
        "gs://bucket/processed/",
    )

    client.load_table_from_uri.assert_called_once()
    args, kwargs = client.load_table_from_uri.call_args
    assert args == (
        "gs://bucket/processed/*.parquet",
        "project.dataset.trips",
    )
    assert isinstance(kwargs["job_config"], bigquery.LoadJobConfig)
    client.load_table_from_uri.return_value.result.assert_called_once_with()
