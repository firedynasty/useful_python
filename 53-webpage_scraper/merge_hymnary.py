"""
Merge duplicate First Lines in the hymnary CSV by combining Hymn # values.
Example: #24 and #24A with same First Line -> "#24, #24A"
"""

import csv

INPUT_FILE = "hymnary_h1955_all_topics.csv"
OUTPUT_FILE = "hymnary_h1955_merged.csv"


def main():
    with open(INPUT_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"Total rows before merge: {len(rows)}")

    # Group by (Topic, Sub-Topic, First Line) and combine Hymn #
    merged = {}
    for row in rows:
        key = (row["Topic"], row["Sub-Topic"], row["First Line"])
        if key in merged:
            existing_nums = merged[key]["Hymn #"]
            new_num = row["Hymn #"]
            if new_num not in existing_nums.split(", "):
                merged[key]["Hymn #"] = f"{existing_nums}, {new_num}"
        else:
            merged[key] = dict(row)

    merged_rows = list(merged.values())
    print(f"Total rows after merge: {len(merged_rows)}")
    print(f"Duplicates merged: {len(rows) - len(merged_rows)}")

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Topic", "Sub-Topic", "Hymn #", "First Line"])
        writer.writeheader()
        writer.writerows(merged_rows)

    print(f"\nSaved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
