from datetime import datetime
from zoneinfo import ZoneInfo

from chatcheckin.message_parser import parse_exported_message, parse_message


SUBMIT_TIME = datetime(2026, 7, 19, 20, 0, tzinfo=ZoneInfo("Asia/Shanghai"))


def parse(content: str, *, submit_time=SUBMIT_TIME):
    return parse_message(person="测试成员", submit_time=submit_time, content=content)


def test_normal_checkin():
    records = parse("打卡：篮球1.5h")
    assert len(records) == 1
    assert records[0].record_type == "NORMAL_CHECKIN"
    assert records[0].activity_content == "篮球1.5h"
    assert records[0].counted is True


def test_normal_checkin_without_colon():
    assert parse("打卡篮球1.5h")[0].activity_content == "篮球1.5h"


def test_missing_normal_content():
    record = parse("打卡：")[0]
    assert record.record_type == "CHECKIN_MISSING_CONTENT"
    assert record.counted is False


def test_standalone_makeup():
    record = parse("补卡：周五 篮球1.5h")[0]
    assert record.record_type == "MAKEUP_CHECKIN"
    assert record.training_date.isoformat() == "2026-07-17"


def test_sample_compact_makeup_syntax():
    submit_time = datetime(2026, 7, 8, 20, 0, tzinfo=ZoneInfo("Asia/Shanghai"))
    record = parse("补卡昨天：基本功1h", submit_time=submit_time)[0]
    assert record.training_date.isoformat() == "2026-07-07"


def test_future_weekday_is_not_reinterpreted():
    submit_time = datetime(2026, 7, 15, 20, 0, tzinfo=ZoneInfo("Asia/Shanghai"))
    record = parse("补卡：周五 篮球1.5h", submit_time=submit_time)[0]
    assert record.record_type == "MAKEUP_DATE_AMBIGUOUS"
    assert record.training_date is None
    assert record.counted is False


def test_embedded_makeup_creates_two_records():
    records = parse("打卡：健身1h,补周五：基本功1h")
    assert [record.record_type for record in records] == [
        "NORMAL_CHECKIN",
        "MAKEUP_CHECKIN",
    ]


def test_multiple_embedded_makeups():
    records = parse("打卡：健身1h，补昨天：跑步0.5h，补上周五：篮球1.5h")
    assert len(records) == 3
    assert all(record.counted for record in records)


def test_unmatched_text_is_retained():
    record = parse("今天练了投篮")[0]
    assert record.record_type == "UNMATCHED_TEXT"
    assert record.original_content == "今天练了投篮"


def test_image_message_is_not_counted():
    record = parse_message(
        person="测试成员",
        submit_time=SUBMIT_TIME,
        content="",
        source_message_type="图片消息",
    )[0]
    assert record.record_type == "IMAGE_UNRECOGNIZED"
    assert record.activity_content == "图片"


def test_exported_message_uses_observed_schema():
    message = {
        "platformMessageId": "abc123",
        "createTime": 1783842295,
        "formattedTime": "2026-07-12 15:44:55",
        "type": "文本消息",
        "content": "打卡 健身1h",
        "rawContent": "wxid_example:\n打卡 健身1h",
        "senderUsername": "wxid_example",
        "senderDisplayName": "宓姝廷",
    }
    record = parse_exported_message(message)[0]
    assert record.person == "宓姝廷"
    assert record.submit_time.isoformat() == "2026-07-12T15:44:55+08:00"
    assert record.message_id == "abc123"
