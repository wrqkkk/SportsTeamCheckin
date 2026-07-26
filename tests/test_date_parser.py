from datetime import date

import pytest

from chatcheckin.date_parser import resolve_date_expression


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("昨天", date(2026, 7, 18)),
        ("昨日", date(2026, 7, 18)),
        ("前天", date(2026, 7, 17)),
        ("周五", date(2026, 7, 17)),
        ("上周五", date(2026, 7, 10)),
        ("2026-07-10", date(2026, 7, 10)),
        ("2026年7月10日", date(2026, 7, 10)),
        ("7月10日", date(2026, 7, 10)),
    ],
)
def test_resolve_supported_dates(expression, expected):
    result = resolve_date_expression(expression, date(2026, 7, 19))
    assert result.record_type == "MAKEUP_CHECKIN"
    assert result.training_date == expected


def test_current_week_future_weekday_is_ambiguous():
    result = resolve_date_expression("周五", date(2026, 7, 15))
    assert result.record_type == "MAKEUP_DATE_AMBIGUOUS"
    assert result.training_date is None


def test_same_day_weekday_is_ambiguous():
    result = resolve_date_expression("周五", date(2026, 7, 17))
    assert result.record_type == "MAKEUP_DATE_AMBIGUOUS"


def test_previous_week_crosses_year_boundary():
    result = resolve_date_expression("上周五", date(2027, 1, 4))
    assert result.training_date == date(2027, 1, 1)


def test_unsupported_expression_is_unresolved():
    result = resolve_date_expression("上周 篮球", date(2026, 7, 19))
    assert result.record_type == "MAKEUP_DATE_UNRESOLVED"
