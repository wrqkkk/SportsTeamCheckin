from datetime import datetime
from zoneinfo import ZoneInfo

from chatcheckin.message_parser import parse_message
from chatcheckin.reporting import apply_deduplication, member_week_counts


TIME = datetime(2026, 7, 19, 20, 0, tzinfo=ZoneInfo("Asia/Shanghai"))


def test_duplicate_member_date_counts_once():
    first = parse_message(person="A", submit_time=TIME, content="打卡：篮球1h")[0]
    second = parse_message(person="A", submit_time=TIME, content="打卡：跑步1h")[0]
    records = apply_deduplication([first, second])
    assert records[0].counted is True
    assert records[0].dedup_status == "PRIMARY"
    assert records[1].counted is False
    assert records[1].dedup_status == "DUPLICATE"


def test_member_week_counts_uses_unique_dates():
    day1 = parse_message(person="A", submit_time=TIME, content="打卡：篮球1h")[0]
    day2_time = TIME.replace(day=18)
    day2 = parse_message(person="A", submit_time=day2_time, content="打卡：健身1h")[0]
    _, weeks, counts = member_week_counts(apply_deduplication([day1, day2]))
    assert len(weeks) == 1
    assert counts[("A", weeks[0])] == 2
