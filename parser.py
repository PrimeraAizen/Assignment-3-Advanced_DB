import csv
import json
import sys

def csv_to_json(csv_file, json_file):
    with open(csv_file, "r") as f:
        reader = csv.DictReader(f)
        logs = []
        for row in reader:
            logs.append({
                "URL": row["URL"],
                "IP": row["IP"],
                "timeStamp": row["timeStamp"],   
                "timeSpent": int(row["timeSpent"])
            })

    with open(json_file, "w") as f:
        json.dump(logs, f, indent=4)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python csv_to_json.py input.csv output.json")
    else:
        csv_to_json(sys.argv[1], sys.argv[2])
