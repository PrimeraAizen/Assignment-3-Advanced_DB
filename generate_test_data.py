#!/usr/bin/env python3
"""
Generate test data for MongoDB sharding demonstration
Creates a large CSV file with random log entries
"""

import csv
import random
from datetime import datetime, timedelta
import sys


def generate_test_data(num_records=10000, output_file="test_large.csv"):
    """Generate test log data"""

    print(f"Generating {num_records:,} test records...")

    # Sample data
    urls = [
        "https://example.com/home",
        "https://example.com/about",
        "https://example.com/products",
        "https://example.com/contact",
        "https://example.com/blog",
        "https://example.com/login",
        "https://example.com/signup",
        "https://example.com/dashboard",
        "https://example.com/profile",
        "https://example.com/settings",
        "https://api.example.com/v1/users",
        "https://api.example.com/v1/products",
        "https://api.example.com/v1/orders",
        "https://cdn.example.com/images",
        "https://cdn.example.com/scripts",
    ]

    # Generate realistic IP addresses
    def random_ip():
        return f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 255)}"

    # Generate realistic timestamps
    start_date = datetime(2024, 1, 1)

    with open(output_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["URL", "IP", "timeStamp", "timeSpent"])

        for i in range(num_records):
            url = random.choice(urls)
            ip = random_ip()

            # Random timestamp within the last year
            days_offset = random.randint(0, 365)
            hours_offset = random.randint(0, 23)
            minutes_offset = random.randint(0, 59)
            seconds_offset = random.randint(0, 59)

            timestamp = start_date + timedelta(
                days=days_offset,
                hours=hours_offset,
                minutes=minutes_offset,
                seconds=seconds_offset,
            )
            timestamp_str = timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")

            # Random time spent (in milliseconds)
            time_spent = random.randint(100, 30000)

            writer.writerow([url, ip, timestamp_str, time_spent])

            # Progress indicator
            if (i + 1) % 1000 == 0:
                print(f"  Generated {i + 1:,} records...")

    print(f"✅ Successfully generated {num_records:,} records in {output_file}")

    # Show file size
    import os

    size_bytes = os.path.getsize(output_file)
    size_mb = size_bytes / (1024 * 1024)
    print(f"   File size: {size_mb:.2f} MB")

    # Estimate MongoDB size
    # CSV is more compact than JSON/BSON
    estimated_mongo_size = size_mb * 1.5  # Rough estimate
    print(f"   Estimated MongoDB size: ~{estimated_mongo_size:.2f} MB")

    if estimated_mongo_size < 1:
        print(
            f"\n⚠️  Warning: Even {num_records:,} records (~{estimated_mongo_size:.2f} MB)"
        )
        print("   may not trigger automatic chunk splitting (needs ~1-2 MB minimum)")
        print("\n   Recommendations:")
        print("   - Use 5,000+ records for 1 MB chunk size")
        print("   - Use 100,000+ records for default 64 MB chunks")
        print("   - Or use manual chunk splitting")
    else:
        print(f"\n✅ This dataset should work well with 1 MB chunk size!")


if __name__ == "__main__":
    num_records = 10000  # Default

    if len(sys.argv) > 1:
        try:
            num_records = int(sys.argv[1])
        except ValueError:
            print("Usage: python generate_test_data.py [num_records]")
            print("Example: python generate_test_data.py 50000")
            sys.exit(1)

    output_file = (
        f"test_{num_records}.csv" if num_records != 10000 else "test_large.csv"
    )

    generate_test_data(num_records, output_file)

    print("\nNext steps:")
    print(f"1. python parser.py {output_file} output_large.json")
    print("2. ./setup_and_import.sh")
    print("3. ./quick_test.sh")
