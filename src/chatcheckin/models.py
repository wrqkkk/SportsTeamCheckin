from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


@dataclass
class CheckinRecord:
    """Structured check-in record."""

    person: str
    submit_time: datetime
    submission_date: date
    training_date: Optional[date]
    activity_content: str
    record_type: str
    counted: bool
    original_content: str
    resolution_note: Optional[str] = None
