from datetime import date, timedelta


WEEKDAY_MAP = {
    "周一": 0,
    "周二": 1,
    "周三": 2,
    "周四": 3,
    "周五": 4,
    "周六": 5,
    "周日": 6,
    "周天": 6,
}


def monday_of_week(day: date) -> date:
    return day - timedelta(days=day.weekday())


def resolve_relative_day(expression: str, submission_date: date):
    if expression in {"昨天", "昨日"}:
        return submission_date - timedelta(days=1)
    if expression == "前天":
        return submission_date - timedelta(days=2)
    return None


def validate_makeup_date(training_date: date, submission_date: date):
    """Makeup records must refer to a past date."""
    return training_date < submission_date
