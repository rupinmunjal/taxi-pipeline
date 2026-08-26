from datetime import date

import pytest

from pipeline.config import parse_pickup_date_window


def test_parse_pickup_date_window():
    assert parse_pickup_date_window("2026-05-01", "2026-06-01") == (
        date(2026, 5, 1),
        date(2026, 6, 1),
    )


@pytest.mark.parametrize(
    ("start", "end"),
    [
        ("2026-05-01", None),
        ("not-a-date", "2026-06-01"),
        ("2026-06-01", "2026-05-01"),
    ],
)
def test_parse_pickup_date_window_rejects_invalid_configuration(start, end):
    with pytest.raises(ValueError):
        parse_pickup_date_window(start, end)
