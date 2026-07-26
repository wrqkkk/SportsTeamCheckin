from collections import defaultdict
from dataclasses import replace
from datetime import date, timedelta
from typing import Iterable, Sequence

from .date_parser import monday_of_week
from .models import CheckinRecord


def apply_deduplication(records: Sequence[CheckinRecord]) -> list[CheckinRecord]:
    """Keep the first counted record per member and training date."""

    seen: dict[tuple[str, date], str | None] = {}
    output: list[CheckinRecord] = []
    for record in records:
        if not record.counted or record.training_date is None:
            output.append(replace(record, dedup_status="NOT_APPLICABLE"))
            continue

        key = (record.person, record.training_date)
        if key not in seen:
            seen[key] = record.message_id
            output.append(replace(record, dedup_status="PRIMARY"))
            continue

        first_message_id = seen[key]
        note = record.resolution_note or ""
        duplicate_note = (
            f"Duplicate check-in for {record.person} on "
            f"{record.training_date.isoformat()}."
        )
        if first_message_id:
            duplicate_note += f" First message ID: {first_message_id}."
        output.append(
            replace(
                record,
                counted=False,
                dedup_status="DUPLICATE",
                resolution_note=f"{note} {duplicate_note}".strip(),
            )
        )
    return output


def sorted_weeks(records: Iterable[CheckinRecord]) -> list[date]:
    """Return sorted Monday dates represented by counted records."""

    return sorted(
        {
            monday_of_week(record.training_date)
            for record in records
            if record.counted and record.training_date is not None
        }
    )


def member_week_counts(
    records: Iterable[CheckinRecord],
) -> tuple[list[str], list[date], dict[tuple[str, date], int]]:
    """Count unique check-in dates by member and Monday-based week."""

    records = list(records)
    members = sorted({record.person for record in records if record.counted})
    weeks = sorted_weeks(records)
    dates_by_key: dict[tuple[str, date], set[date]] = defaultdict(set)
    for record in records:
        if record.counted and record.training_date is not None:
            week = monday_of_week(record.training_date)
            dates_by_key[(record.person, week)].add(record.training_date)
    counts = {key: len(days) for key, days in dates_by_key.items()}
    return members, weeks, counts


def weekly_activity_grid(
    records: Iterable[CheckinRecord], week_start: date
) -> dict[tuple[str, date], str]:
    """Join activity content for each member/day in one week."""

    week_end = week_start + timedelta(days=6)
    activities: dict[tuple[str, date], list[str]] = defaultdict(list)
    for record in records:
        if (
            record.counted
            and record.training_date is not None
            and week_start <= record.training_date <= week_end
        ):
            activities[(record.person, record.training_date)].append(
                record.activity_content
            )
    return {key: "；".join(values) for key, values in activities.items()}
