"""FastAPI application exposing cached taxi analytics."""

import logging
import os
from datetime import date
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from google.api_core.exceptions import GoogleAPIError
from google.cloud import bigquery

from api import analytics
from api.bigquery_client import BQ_TABLE_ID, get_bigquery_client
from api.models import DateRange, DurationByWeekday, Health, RevenueByWeekday, Summary, TopZone

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Taxi Pipeline Analytics API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


def get_date_range(
    start_date: Annotated[date | None, Query()] = None,
    end_date: Annotated[date | None, Query()] = None,
) -> DateRange:
    """Validate the optional inclusive date range."""
    if (start_date is None) != (end_date is None):
        raise HTTPException(
            status_code=422,
            detail="start_date and end_date must be supplied together",
        )
    if start_date and end_date and end_date < start_date:
        raise HTTPException(
            status_code=422,
            detail="end_date must be on or after start_date",
        )
    return DateRange(start_date=start_date, end_date=end_date)


def _dates(date_range: DateRange) -> tuple[date | None, date | None]:
    return date_range.start_date, date_range.end_date


def _run(handler):
    try:
        return handler()
    except GoogleAPIError as exc:
        logger.exception("BigQuery request failed")
        raise HTTPException(status_code=503, detail="BigQuery request failed") from exc


Client = Annotated[bigquery.Client, Depends(get_bigquery_client)]
Dates = Annotated[DateRange, Depends(get_date_range)]


@app.get("/api/revenue-by-weekday", response_model=list[RevenueByWeekday])
def get_revenue_by_weekday(client: Client, date_range: Dates):
    """Return weekday revenue using the optional ``pickup_date`` filter."""
    return _run(
        lambda: analytics.revenue_by_weekday(client, BQ_TABLE_ID, _dates(date_range))
    )


@app.get("/api/duration-by-weekday", response_model=list[DurationByWeekday])
def get_duration_by_weekday(client: Client, date_range: Dates):
    """Return weekday duration using the optional ``pickup_date`` filter."""
    return _run(
        lambda: analytics.duration_by_weekday(client, BQ_TABLE_ID, _dates(date_range))
    )


@app.get("/api/top-zones", response_model=list[TopZone])
def get_top_zones(client: Client, date_range: Dates):
    """Return top zones using the optional ``pickup_date`` filter."""
    return _run(lambda: analytics.top_zones(client, BQ_TABLE_ID, _dates(date_range)))


@app.get("/api/summary", response_model=Summary)
def get_summary(client: Client, date_range: Dates):
    """Return summary values using the optional ``pickup_date`` filter."""
    return _run(lambda: analytics.summary(client, BQ_TABLE_ID, _dates(date_range)))


@app.get("/api/health", response_model=Health)
def get_health(client: Client, date_range: Dates):
    """Check BigQuery access using the optional ``pickup_date`` filter."""
    return _run(lambda: analytics.health(client, BQ_TABLE_ID, _dates(date_range)))
