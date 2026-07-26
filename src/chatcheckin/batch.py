import csv
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional, Sequence

from .message_parser import parse_exported_message
from .models import CheckinRecord


def load_export(path: str | Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Load a WeChat JSON export and return metadata plus messages."""

    source_path = Path(path)
    try:
        with source_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Unable to read JSON export: {source_path}") from exc

    if isinstance(payload, list):
        return {}, payload
    if not isinstance(payload, dict):
        raise ValueError("The JSON root must be an object or an array of messages.")

    messages = payload.get("messages")
    if not isinstance(messages, list):
        raise ValueError("The JSON object must contain a 'messages' array.")

    metadata = {key: value for key, value in payload.items() if key != "messages"}
    return metadata, messages


def parse_export(
    messages: Sequence[Mapping[str, Any]],
    *,
    timezone_name: str = "Asia/Shanghai",
    reporting_year: Optional[int] = None,
    aliases: Optional[Mapping[str, str]] = None,
) -> list[CheckinRecord]:
    """Parse all messages while preserving message order."""

    records: list[CheckinRecord] = []
    for message in messages:
        records.extend(
            parse_exported_message(
                message,
                timezone_name=timezone_name,
                reporting_year=reporting_year,
                aliases=aliases,
            )
        )
    return records


def write_records_csv(records: Iterable[CheckinRecord], path: str | Path) -> Path:
    """Write auditable records to UTF-8 CSV with an Excel-friendly BOM."""

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "message_id",
        "person",
        "sender_username",
        "submit_time",
        "submission_date",
        "training_date",
        "activity_content",
        "record_type",
        "counted",
        "source_message_type",
        "original_content",
        "raw_content",
        "resolution_note",
        "dedup_status",
    ]
    with output_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow(record.to_dict())
    return output_path
