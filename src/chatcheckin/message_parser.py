import re
from datetime import datetime
from typing import Any, Mapping, Optional
from zoneinfo import ZoneInfo

from .date_parser import (
    FULL_DATE_TOKEN,
    MONTH_DAY_TOKEN,
    PREVIOUS_WEEK_TOKEN,
    RELATIVE_DAY_TOKEN,
    WEEKDAY_TOKEN,
    resolve_date_expression,
)
from .models import CheckinRecord

DATE_TOKEN = (
    rf"(?:{FULL_DATE_TOKEN}|{MONTH_DAY_TOKEN}|{PREVIOUS_WEEK_TOKEN}|"
    rf"{RELATIVE_DAY_TOKEN}|{WEEKDAY_TOKEN})"
)
EMBEDDED_MAKEUP_PATTERN = re.compile(
    rf"(?P<prefix>补卡|补)\s*[:：]?\s*(?P<date>{DATE_TOKEN})"
)
LEADING_SEPARATORS = " \t\r\n:：,，;；"
TEXT_MESSAGE_TYPES = {"文本消息", "引用消息", "text"}
NON_TEXT_RECORD_TYPES = {
    "图片消息": ("IMAGE_UNRECOGNIZED", "图片"),
    "语音消息": ("VOICE_UNRECOGNIZED", "语音"),
    "视频消息": ("VIDEO_UNRECOGNIZED", "视频"),
    "文件消息": ("FILE_UNRECOGNIZED", "文件"),
}


def _record(
    *,
    person: str,
    submit_time: datetime,
    training_date,
    activity_content: str,
    record_type: str,
    counted: bool,
    original_content: str,
    resolution_note: Optional[str],
    message_id: Optional[str],
    sender_username: Optional[str],
    source_message_type: str,
    raw_content: Optional[str],
) -> CheckinRecord:
    return CheckinRecord(
        person=person,
        submit_time=submit_time,
        submission_date=submit_time.date(),
        training_date=training_date,
        activity_content=activity_content,
        record_type=record_type,
        counted=counted,
        original_content=original_content,
        resolution_note=resolution_note,
        message_id=message_id,
        sender_username=sender_username,
        source_message_type=source_message_type,
        raw_content=raw_content,
    )


def _parse_makeup_segment(
    segment: str,
    *,
    person: str,
    submit_time: datetime,
    original_content: str,
    reporting_year: Optional[int],
    message_id: Optional[str],
    sender_username: Optional[str],
    source_message_type: str,
    raw_content: Optional[str],
) -> CheckinRecord:
    segment = segment.strip(LEADING_SEPARATORS)
    if segment.startswith("补卡"):
        date_and_content = segment[2:].lstrip(LEADING_SEPARATORS)
    elif segment.startswith("补"):
        date_and_content = segment[1:].lstrip(LEADING_SEPARATORS)
    else:
        date_and_content = segment

    resolution = resolve_date_expression(
        date_and_content,
        submit_time.date(),
        reporting_year=reporting_year,
    )
    matched_length = len(resolution.matched_text or "")
    activity_content = date_and_content[matched_length:].strip(LEADING_SEPARATORS)

    record_type = resolution.record_type
    counted = record_type == "MAKEUP_CHECKIN" and bool(activity_content)
    if record_type == "MAKEUP_CHECKIN" and not activity_content:
        record_type = "MAKEUP_MISSING_CONTENT"

    return _record(
        person=person,
        submit_time=submit_time,
        training_date=resolution.training_date,
        activity_content=activity_content,
        record_type=record_type,
        counted=counted,
        original_content=original_content,
        resolution_note=resolution.note,
        message_id=message_id,
        sender_username=sender_username,
        source_message_type=source_message_type,
        raw_content=raw_content,
    )


def parse_message(
    *,
    person: str,
    submit_time: datetime,
    content: str,
    source_message_type: str = "文本消息",
    reporting_year: Optional[int] = None,
    message_id: Optional[str] = None,
    sender_username: Optional[str] = None,
    raw_content: Optional[str] = None,
) -> list[CheckinRecord]:
    """Parse one normalized source message into zero or more records."""

    original_content = content or ""
    normalized = original_content.strip()

    if source_message_type not in TEXT_MESSAGE_TYPES:
        record_type, label = NON_TEXT_RECORD_TYPES.get(
            source_message_type,
            ("OTHER_UNRECOGNIZED", source_message_type or "其他消息"),
        )
        return [
            _record(
                person=person,
                submit_time=submit_time,
                training_date=None,
                activity_content=label,
                record_type=record_type,
                counted=False,
                original_content=original_content,
                resolution_note="The message type is outside the V1 text parser.",
                message_id=message_id,
                sender_username=sender_username,
                source_message_type=source_message_type,
                raw_content=raw_content,
            )
        ]

    if normalized.startswith("补卡"):
        return [
            _parse_makeup_segment(
                normalized,
                person=person,
                submit_time=submit_time,
                original_content=original_content,
                reporting_year=reporting_year,
                message_id=message_id,
                sender_username=sender_username,
                source_message_type=source_message_type,
                raw_content=raw_content,
            )
        ]

    if not normalized.startswith("打卡"):
        return [
            _record(
                person=person,
                submit_time=submit_time,
                training_date=None,
                activity_content=normalized,
                record_type="UNMATCHED_TEXT",
                counted=False,
                original_content=original_content,
                resolution_note="The text does not begin with a supported V1 prefix.",
                message_id=message_id,
                sender_username=sender_username,
                source_message_type=source_message_type,
                raw_content=raw_content,
            )
        ]

    body = normalized[2:].lstrip(LEADING_SEPARATORS)
    matches = list(EMBEDDED_MAKEUP_PATTERN.finditer(body))
    records: list[CheckinRecord] = []

    normal_content = body[: matches[0].start()] if matches else body
    normal_content = normal_content.strip(LEADING_SEPARATORS)
    if normal_content:
        records.append(
            _record(
                person=person,
                submit_time=submit_time,
                training_date=submit_time.date(),
                activity_content=normal_content,
                record_type="NORMAL_CHECKIN",
                counted=True,
                original_content=original_content,
                resolution_note="Assigned to the submission date.",
                message_id=message_id,
                sender_username=sender_username,
                source_message_type=source_message_type,
                raw_content=raw_content,
            )
        )

    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        segment = body[match.start() : end]
        records.append(
            _parse_makeup_segment(
                segment,
                person=person,
                submit_time=submit_time,
                original_content=original_content,
                reporting_year=reporting_year,
                message_id=message_id,
                sender_username=sender_username,
                source_message_type=source_message_type,
                raw_content=raw_content,
            )
        )

    if not records:
        records.append(
            _record(
                person=person,
                submit_time=submit_time,
                training_date=submit_time.date(),
                activity_content="",
                record_type="CHECKIN_MISSING_CONTENT",
                counted=False,
                original_content=original_content,
                resolution_note="The check-in prefix has no activity content.",
                message_id=message_id,
                sender_username=sender_username,
                source_message_type=source_message_type,
                raw_content=raw_content,
            )
        )

    return records


def _parse_submit_time(message: Mapping[str, Any], timezone_name: str) -> datetime:
    timezone = ZoneInfo(timezone_name)
    formatted_time = message.get("formattedTime")
    if isinstance(formatted_time, str) and formatted_time.strip():
        try:
            parsed = datetime.strptime(formatted_time.strip(), "%Y-%m-%d %H:%M:%S")
            return parsed.replace(tzinfo=timezone)
        except ValueError:
            pass

    timestamp = message.get("createTime")
    if isinstance(timestamp, (int, float)):
        return datetime.fromtimestamp(timestamp, tz=timezone)

    raise ValueError("Message has neither a valid formattedTime nor createTime.")


def parse_exported_message(
    message: Mapping[str, Any],
    *,
    timezone_name: str = "Asia/Shanghai",
    reporting_year: Optional[int] = None,
    aliases: Optional[Mapping[str, str]] = None,
) -> list[CheckinRecord]:
    """Parse one message from the observed WeChat JSON export schema."""

    submit_time = _parse_submit_time(message, timezone_name)
    display_name = str(message.get("senderDisplayName") or "").strip()
    person = aliases.get(display_name, display_name) if aliases else display_name
    if not person:
        person = str(message.get("senderUsername") or "UNKNOWN_SENDER")

    return parse_message(
        person=person,
        submit_time=submit_time,
        content=str(message.get("content") or ""),
        source_message_type=str(message.get("type") or "其他消息"),
        reporting_year=reporting_year,
        message_id=(
            str(message.get("platformMessageId"))
            if message.get("platformMessageId") is not None
            else None
        ),
        sender_username=(
            str(message.get("senderUsername"))
            if message.get("senderUsername") is not None
            else None
        ),
        raw_content=(
            str(message.get("rawContent"))
            if message.get("rawContent") is not None
            else None
        ),
    )
