from datetime import date

from chatcheckin.date_parser import resolve_relative_day, validate_makeup_date


def test_yesterday():
    assert resolve_relative_day("昨天", date(2026, 7, 19)) == date(2026, 7, 18)


def test_before_submission():
    assert validate_makeup_date(date(2026, 7, 17), date(2026, 7, 19)) is True


def test_future_makeup_is_invalid():
    assert validate_makeup_date(date(2026, 7, 17), date(2026, 7, 15)) is False
