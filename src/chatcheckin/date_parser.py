import re
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional


WEEKDAY_MAP = {
    "周一": 0,
    "星期一": 0,
    "周二": 1,
    "星期二": 1,
    "周三": 2,
    "星期三": 2,
    "周四": 3,
    "星期四": 3,
    "周五": 4,
    "星期五": 4,
    "周六": 5,
    "星期六": 5,
    "周日": 6,
    "周天": 6,
    "星期日": 6,
    "星期天": 6,
}

WEEKDAY_TOKEN = r"(?:星期[一二三四五六日天]|周[一二三四五六日天])"
PREVIOUS_WEEK_TOKEN = r"上周[一二三四五六日天]"
RELATIVE_DAY_TOKEN = r"(?:昨天|昨日|前天)"
FULL_DATE_TOKEN = (
    r"(?:\d{4}年\d{1,2}月\d{1,2}[日号]?|"
    r"\d{4}[-/.]\d{1,2}[-/.]\d{1,2})"
)
MONTH_DAY_TOKEN = (
    r"(?:\d{1,2}月\d{1,2}[日号]?|"
    r"\d{1,2}[-/.]\d{1,2})"
)
DATE_EXPRESSION_PATTERN = re.compile(
    rf"^(?P<date>{FULL_DATE_TOKEN}|{MONTH_DAY_TOKEN}|"
    rf"{PREVIOUS_WEEK_TOKEN}|{RELATIVE_DAY_TOKEN}|{WEEKDAY_TOKEN})"
)


@dataclass(frozen=True)
class DateResolution:
    """Result of resolving one supported date expression."""

    matched_text: Optional[str]
    training_date: Optional[date]
    record_type: str
    note: str


class InvalidDateExpression(ValueError):
    """Raised internally when a syntactically matched date is invalid."""


def monday_of_week(day: date) -> date:
    """Return Monday of the Monday-to-Sunday week containing ``day``."""

    return day - timedelta(days=day.weekday())


def resolve_relative_day(expression: str, submission_date: date) -> Optional[date]:
    """Resolve the supported relative-day expressions."""

    if expression in {"昨天", "昨日"}:
        return submission_date - timedelta(days=1)
    if expression == "前天":
        return submission_date - timedelta(days=2)
    return None


def validate_makeup_date(training_date: date, submission_date: date) -> bool:
    """Return whether a makeup record refers strictly to the past."""

    return training_date < submission_date


def _parse_full_date(expression: str) -> date:
    if "年" in expression:
        match = re.fullmatch(r"(\d{4})年(\d{1,2})月(\d{1,2})[日号]?", expression)
    else:
        match = re.fullmatch(r"(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})", expression)
    if match is None:
        raise InvalidDateExpression(expression)
    try:
        return date(*(int(value) for value in match.groups()))
    except ValueError as exc:
        raise InvalidDateExpression(expression) from exc


def _parse_month_day(expression: str, year: int) -> date:
    if "月" in expression:
        match = re.fullmatch(r"(\d{1,2})月(\d{1,2})[日号]?", expression)
    else:
        match = re.fullmatch(r"(\d{1,2})[-/.](\d{1,2})", expression)
    if match is None:
        raise InvalidDateExpression(expression)
    month, day_of_month = (int(value) for value in match.groups())
    try:
        return date(year, month, day_of_month)
    except ValueError as exc:
        raise InvalidDateExpression(expression) from exc


def _resolve_weekday(expression: str, submission_date: date) -> date:
    week_start = monday_of_week(submission_date)
    return week_start + timedelta(days=WEEKDAY_MAP[expression])


def _resolve_previous_weekday(expression: str, submission_date: date) -> date:
    weekday_expression = "周" + expression[-1]
    previous_week_start = monday_of_week(submission_date) - timedelta(days=7)
    return previous_week_start + timedelta(days=WEEKDAY_MAP[weekday_expression])


def resolve_date_expression(
    text: str,
    submission_date: date,
    *,
    reporting_year: Optional[int] = None,
) -> DateResolution:
    """Resolve a supported date expression at the beginning of ``text``.

    The matching order follows ``docs/rules.md``: full dates, month-day dates,
    previous-week weekdays, relative days, and current-week weekdays.
    """

    candidate = text.lstrip()
    match = DATE_EXPRESSION_PATTERN.match(candidate)
    if match is None:
        return DateResolution(
            matched_text=None,
            training_date=None,
            record_type="MAKEUP_DATE_UNRESOLVED",
            note="No supported date expression was found.",
        )

    expression = match.group("date")
    try:
        if re.fullmatch(FULL_DATE_TOKEN, expression):
            resolved_date = _parse_full_date(expression)
        elif re.fullmatch(MONTH_DAY_TOKEN, expression):
            resolved_date = _parse_month_day(
                expression,
                reporting_year if reporting_year is not None else submission_date.year,
            )
        elif re.fullmatch(PREVIOUS_WEEK_TOKEN, expression):
            resolved_date = _resolve_previous_weekday(expression, submission_date)
        elif re.fullmatch(RELATIVE_DAY_TOKEN, expression):
            relative_date = resolve_relative_day(expression, submission_date)
            if relative_date is None:
                raise InvalidDateExpression(expression)
            resolved_date = relative_date
        else:
            resolved_date = _resolve_weekday(expression, submission_date)
    except InvalidDateExpression:
        return DateResolution(
            matched_text=expression,
            training_date=None,
            record_type="MAKEUP_DATE_UNRESOLVED",
            note=f"The date expression '{expression}' is invalid.",
        )

    if not validate_makeup_date(resolved_date, submission_date):
        return DateResolution(
            matched_text=expression,
            training_date=None,
            record_type="MAKEUP_DATE_AMBIGUOUS",
            note=(
                f"The resolved date {resolved_date.isoformat()} is not earlier than "
                f"the submission date {submission_date.isoformat()}."
            ),
        )

    return DateResolution(
        matched_text=expression,
        training_date=resolved_date,
        record_type="MAKEUP_CHECKIN",
        note=f"Resolved '{expression}' to {resolved_date.isoformat()}.",
    )
