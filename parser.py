import csv
import json
import sys
import re

# Regex patterns for validation
URL_PATTERN = re.compile(
    r"^https?://"  # http:// or https://
    r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain...
    r"localhost|"  # localhost...
    r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
    r"(?::\d+)?"  # optional port
    r"(?:/?|[/?]\S+)$",
    re.IGNORECASE,
)

IP_PATTERN = re.compile(
    r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"
    r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
)

# Timestamp pattern: YYYY-MM-DDTHH:MM:SSZ or similar formats
TIMESTAMP_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def validate_url(url):
    """Validate URL format"""
    return bool(URL_PATTERN.match(url))


def validate_ip(ip):
    """Validate IP address format"""
    return bool(IP_PATTERN.match(ip))


def validate_timestamp(timestamp):
    """Validate timestamp format (YYYY-MM-DD HH:MM:SS)"""
    return bool(TIMESTAMP_PATTERN.match(timestamp))


def csv_to_json(csv_file, json_file):
    with open(csv_file, "r") as f:
        reader = csv.DictReader(f)
        logs = []
        invalid_rows = []
        row_number = 1  # Start from 1 (excluding header)

        for row in reader:
            row_number += 1
            errors = []

            # Validate URL
            if not validate_url(row["URL"]):
                errors.append(f"Invalid URL: {row['URL']}")

            # Validate IP
            if not validate_ip(row["IP"]):
                errors.append(f"Invalid IP: {row['IP']}")

            # Validate timestamp
            if not validate_timestamp(row["timeStamp"]):
                errors.append(f"Invalid timestamp: {row['timeStamp']}")

            # Validate timeSpent is numeric
            try:
                time_spent = int(row["timeSpent"])
            except (ValueError, KeyError):
                errors.append(f"Invalid timeSpent: {row.get('timeSpent', 'missing')}")
                time_spent = None

            if errors:
                invalid_rows.append({"row": row_number, "data": row, "errors": errors})
            else:
                logs.append(
                    {
                        "URL": row["URL"],
                        "IP": row["IP"],
                        "timeStamp": row["timeStamp"],
                        "timeSpent": time_spent,
                    }
                )

        # Report invalid rows
        if invalid_rows:
            print(f"\n⚠️  Found {len(invalid_rows)} invalid row(s):")
            for invalid in invalid_rows:
                print(f"\nRow {invalid['row']}:")
                for error in invalid["errors"]:
                    print(f"  - {error}")
            print(f"\n✓ Valid rows: {len(logs)}")
            print(f"✗ Invalid rows: {len(invalid_rows)}")
        else:
            print(f"✓ All {len(logs)} rows are valid!")

    with open(json_file, "w") as f:
        json.dump(logs, f, indent=4)

    print(f"\n✓ Successfully wrote {len(logs)} valid entries to {json_file}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python csv_to_json.py input.csv output.json")
    else:
        csv_to_json(sys.argv[1], sys.argv[2])
