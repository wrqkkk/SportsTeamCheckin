import json

from chatcheckin.batch import load_export, parse_export, write_records_csv


def test_load_parse_and_write_export(tmp_path):
    source = tmp_path / "chat.json"
    source.write_text(
        json.dumps(
            {
                "exportInfo": {"tool": "example"},
                "messages": [
                    {
                        "platformMessageId": "1",
                        "formattedTime": "2026-07-19 20:00:00",
                        "type": "文本消息",
                        "content": "打卡：篮球1.5h",
                        "senderUsername": "wxid_a",
                        "senderDisplayName": "成员A",
                    },
                    {
                        "platformMessageId": "2",
                        "formattedTime": "2026-07-19 20:05:00",
                        "type": "图片消息",
                        "content": "",
                        "senderUsername": "wxid_b",
                        "senderDisplayName": "成员B",
                    },
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    metadata, messages = load_export(source)
    records = parse_export(messages)
    output = write_records_csv(records, tmp_path / "records.csv")

    assert metadata["exportInfo"]["tool"] == "example"
    assert len(records) == 2
    assert records[0].record_type == "NORMAL_CHECKIN"
    assert records[1].record_type == "IMAGE_UNRECOGNIZED"
    assert output.exists()
