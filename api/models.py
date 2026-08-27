"""Typed request helpers and API response models."""

from datetime import date
from typing import Literal

from pydantic import BaseModel


class DateRange(BaseModel):
    """Optional inclusive pickup-date range shared by analytics queries."""

    start_date: date | None = None
    end_date: date | None = None


class RevenueByWeekday(BaseModel):
    """Average trip revenue for one weekday."""

    weekday: str
    avg_revenue: float


class DurationByWeekday(BaseModel):
    """Average trip duration for one weekday."""

    weekday: str
    avg_trip_duration: float


class TopZone(BaseModel):
    """Pickup zone and its total trip revenue."""

    zone_id: int
    revenue: float


class Summary(BaseModel):
    """Header metrics for the selected pickup-date range."""

    total_trips: int
    total_revenue: float
    avg_fare: float


class Health(BaseModel):
    """BigQuery connectivity status."""

    status: Literal["ok"]
