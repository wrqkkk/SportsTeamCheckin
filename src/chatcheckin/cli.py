import argparse
from collections import Counter
from pathlib import Path

from .batch import load_export, parse_export, write_records_csv
from .reporting import apply_deduplication


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="chatcheckin",
        description="Convert an exported WeChat group chat JSON into auditable records.",
    )
    parser.add_argument("input", type=Path, help="Path to the exported JSON file.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("records.csv"),
        help="Output CSV path. Default: records.csv",
    )
    parser.add_argument(
        "--timezone",
        default="Asia/Shanghai",
        help="IANA timezone name. Default: Asia/Shanghai",
    )
    parser.add_argument(
        "--reporting-year",
        type=int,
        default=None,
        help="Year used for month-day makeup dates such as 7月10日.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    _, messages = load_export(args.input)
    records = parse_export(
        messages,
        timezone_name=args.timezone,
        reporting_year=args.reporting_year,
    )
    records = apply_deduplication(records)
    output_path = write_records_csv(records, args.output)
    counts = Counter(record.record_type for record in records)
    counted = sum(record.counted for record in records)
    print(f"Messages: {len(messages)}")
    print(f"Records: {len(records)}")
    print(f"Counted records after deduplication: {counted}")
    print("Record types:")
    for record_type, count in sorted(counts.items()):
        print(f"  {record_type}: {count}")
    print(f"Output: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
