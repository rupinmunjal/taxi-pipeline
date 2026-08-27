from datetime import date

import pytest
from fastapi.testclient import TestClient

from api import analytics
from api.bigquery_client import get_bigquery_client
from api.main import app


class FakeJob:
    total_bytes_processed = 2048

    def __init__(self, rows):
        self.rows = rows

    def result(self):
        return self.rows


class FakeBigQueryClient:
    def __init__(self):
        self.calls = []

    def query(self, sql, job_config):
        self.calls.append((sql, job_config))
        if "AVG(total_amount)" in sql:
            return FakeJob(
                [{"weekday": "Monday", "avg_revenue": 23.5, "weekday_number": 2}]
            )
        if "AVG(trip_duration)" in sql:
            return FakeJob(
                [
                    {
                        "weekday": "Monday",
                        "avg_trip_duration": 14.25,
                        "weekday_number": 2,
                    }
                ]
            )
        if "GROUP BY zone_id" in sql:
            return FakeJob([{"zone_id": 132, "revenue": 1200.5}])
        if "COUNT(*)" in sql:
            return FakeJob(
                [{"total_trips": 100, "total_revenue": 2400.0, "avg_fare": 18.5}]
            )
        return FakeJob([{"f0_": 1}])


@pytest.fixture()
def api_client():
    fake = FakeBigQueryClient()
    analytics.clear_cache()
    app.dependency_overrides[get_bigquery_client] = lambda: fake
    with TestClient(app) as client:
        yield client, fake
    app.dependency_overrides.clear()
    analytics.clear_cache()


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("/api/revenue-by-weekday", [{"weekday": "Monday", "avg_revenue": 23.5}]),
        (
            "/api/duration-by-weekday",
            [{"weekday": "Monday", "avg_trip_duration": 14.25}],
        ),
        ("/api/top-zones", [{"zone_id": 132, "revenue": 1200.5}]),
        (
            "/api/summary",
            {"total_trips": 100, "total_revenue": 2400.0, "avg_fare": 18.5},
        ),
        ("/api/health", {"status": "ok"}),
    ],
)
def test_endpoints_return_typed_responses(api_client, path, expected):
    client, _ = api_client
    response = client.get(path)

    assert response.status_code == 200
    assert response.json() == expected


def test_date_range_uses_query_parameters(api_client):
    client, fake = api_client
    response = client.get(
        "/api/summary?start_date=2026-05-01&end_date=2026-05-31"
    )

    assert response.status_code == 200
    sql, job_config = fake.calls[0]
    assert "pickup_date BETWEEN @start_date AND @end_date" in sql
    assert "2026-05-01" not in sql
    assert [parameter.value for parameter in job_config.query_parameters] == [
        date(2026, 5, 1),
        date(2026, 5, 31),
    ]


def test_partial_or_reversed_date_ranges_are_rejected(api_client):
    client, fake = api_client

    assert client.get("/api/summary?start_date=2026-05-01").status_code == 422
    assert (
        client.get(
            "/api/summary?start_date=2026-05-31&end_date=2026-05-01"
        ).status_code
        == 422
    )
    assert fake.calls == []


def test_identical_requests_use_the_ttl_cache(api_client):
    client, fake = api_client
    url = "/api/top-zones?start_date=2026-05-01&end_date=2026-05-31"

    assert client.get(url).status_code == 200
    assert client.get(url).status_code == 200
    assert len(fake.calls) == 1
