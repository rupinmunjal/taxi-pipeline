"""Cached, parameterized BigQuery analytics queries."""

import logging
from collections.abc import Callable
from datetime import date
from threading import Lock
from typing import TypeVar

from cachetools import TTLCache
from google.cloud import bigquery

from api.models import DurationByWeekday, Health, RevenueByWeekday, Summary, TopZone

logger = logging.getLogger(__name__)

CACHE_TTL_SECONDS = 300
_cache: TTLCache[tuple[str, str | None, str | None], object] = TTLCache(
    maxsize=256,
    ttl=CACHE_TTL_SECONDS,
)
_cache_lock = Lock()
T = TypeVar("T")


def clear_cache() -> None:
    """Clear cached analytics responses, primarily for isolated tests."""
    with _cache_lock:
        _cache.clear()


def _date_filter(date_range: tuple[date | None, date | None]) -> tuple[str, list]:
    start_date, end_date = date_range
    if start_date is None:
        return "", []
    return (
        "WHERE pickup_date BETWEEN @start_date AND @end_date",
        [
            bigquery.ScalarQueryParameter("start_date", "DATE", start_date),
            bigquery.ScalarQueryParameter("end_date", "DATE", end_date),
        ],
    )


def _run_query(
    client: bigquery.Client,
    query_name: str,
    sql: str,
    parameters: list,
):
    job_config = bigquery.QueryJobConfig(query_parameters=parameters)
    job = client.query(sql, job_config=job_config)
    rows = list(job.result())
    logger.info(
        "BigQuery query %s processed %s bytes",
        query_name,
        job.total_bytes_processed or 0,
    )
    return rows


def _cached(
    name: str,
    date_range: tuple[date | None, date | None],
    loader: Callable[[], T],
) -> T:
    key = (
        name,
        date_range[0].isoformat() if date_range[0] else None,
        date_range[1].isoformat() if date_range[1] else None,
    )
    with _cache_lock:
        cached = _cache.get(key)
    if cached is not None:
        return cached  # type: ignore[return-value]

    value = loader()
    with _cache_lock:
        _cache[key] = value
    return value


def revenue_by_weekday(
    client: bigquery.Client,
    table_id: str,
    date_range: tuple[date | None, date | None],
) -> list[RevenueByWeekday]:
    """Average total revenue by weekday, pruned by ``pickup_date`` when set."""
    date_filter, parameters = _date_filter(date_range)
    sql = f"""
        SELECT
            FORMAT_DATE('%A', pickup_date) AS weekday,
            AVG(total_amount) AS avg_revenue,
            EXTRACT(DAYOFWEEK FROM pickup_date) AS weekday_number
        FROM `{table_id}`
        {date_filter}
        GROUP BY weekday, weekday_number
        ORDER BY IF(weekday_number = 1, 7, weekday_number - 1)
    """

    def load() -> list[RevenueByWeekday]:
        rows = _run_query(client, "revenue_by_weekday", sql, parameters)
        return [
            RevenueByWeekday(
                weekday=row["weekday"],
                avg_revenue=float(row["avg_revenue"] or 0),
            )
            for row in rows
        ]

    return _cached("revenue_by_weekday", date_range, load)


def duration_by_weekday(
    client: bigquery.Client,
    table_id: str,
    date_range: tuple[date | None, date | None],
) -> list[DurationByWeekday]:
    """Average duration by weekday, pruned by ``pickup_date`` when set."""
    date_filter, parameters = _date_filter(date_range)
    sql = f"""
        SELECT
            FORMAT_DATE('%A', pickup_date) AS weekday,
            AVG(trip_duration) AS avg_trip_duration,
            EXTRACT(DAYOFWEEK FROM pickup_date) AS weekday_number
        FROM `{table_id}`
        {date_filter}
        GROUP BY weekday, weekday_number
        ORDER BY IF(weekday_number = 1, 7, weekday_number - 1)
    """

    def load() -> list[DurationByWeekday]:
        rows = _run_query(client, "duration_by_weekday", sql, parameters)
        return [
            DurationByWeekday(
                weekday=row["weekday"],
                avg_trip_duration=float(row["avg_trip_duration"] or 0),
            )
            for row in rows
        ]

    return _cached("duration_by_weekday", date_range, load)


def top_zones(
    client: bigquery.Client,
    table_id: str,
    date_range: tuple[date | None, date | None],
) -> list[TopZone]:
    """Top pickup zones by revenue, pruned by ``pickup_date`` when set."""
    date_filter, parameters = _date_filter(date_range)
    sql = f"""
        SELECT
            PULocationID AS zone_id,
            SUM(total_amount) AS revenue
        FROM `{table_id}`
        {date_filter}
        GROUP BY zone_id
        ORDER BY revenue DESC
        LIMIT 10
    """

    def load() -> list[TopZone]:
        rows = _run_query(client, "top_zones", sql, parameters)
        return [
            TopZone(zone_id=int(row["zone_id"]), revenue=float(row["revenue"] or 0))
            for row in rows
            if row["zone_id"] is not None
        ]

    return _cached("top_zones", date_range, load)


def summary(
    client: bigquery.Client,
    table_id: str,
    date_range: tuple[date | None, date | None],
) -> Summary:
    """Summary metrics pruned by the ``pickup_date`` partition when set."""
    date_filter, parameters = _date_filter(date_range)
    sql = f"""
        SELECT
            COUNT(*) AS total_trips,
            COALESCE(SUM(total_amount), 0) AS total_revenue,
            COALESCE(AVG(fare_amount), 0) AS avg_fare
        FROM `{table_id}`
        {date_filter}
    """

    def load() -> Summary:
        row = _run_query(client, "summary", sql, parameters)[0]
        return Summary(
            total_trips=int(row["total_trips"]),
            total_revenue=float(row["total_revenue"]),
            avg_fare=float(row["avg_fare"]),
        )

    return _cached("summary", date_range, load)


def health(
    client: bigquery.Client,
    table_id: str,
    date_range: tuple[date | None, date | None],
) -> Health:
    """Check table access, using the ``pickup_date`` partition when set."""
    date_filter, parameters = _date_filter(date_range)
    sql = f"SELECT 1 FROM `{table_id}` {date_filter} LIMIT 1"
    _run_query(client, "health", sql, parameters)
    return Health(status="ok")
