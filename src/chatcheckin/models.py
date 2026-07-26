from dataclasses import asdict, dataclass
from datetime import date, datetime
from typing import Any, Optional


@dataclass
class CheckinRecord:
    """One auditable record derived from a source message."""

    person: str
    submit_time: datetime
    submission_date: date
    training_date: Optional[date]
    activity_content: str
    record_type: str
    counted: bool
    original_content: str
    resolution_note: Optional[str] = None
    message_id: Optional[str] = None
    sender_username: Optional[str] = None
    source_message_type: str = "文本消息"
    raw_content: Optional[str] = None
    dedup_status: str = "NOT_APPLICABLE"

    def to_dict(self) -> dict[str, Any]:
        """Return a CSV-friendly representation."""

        row = asdict(self)
        row["submit_time"] = self.submit_time.isoformat()
        row["submission_date"] = self.submission_date.isoformat()
        row["training_date"] = (
            self.training_date.isoformat() if self.training_date is not None else ""
        )
        return row
