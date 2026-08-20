"""
clean_courses.py

Normalizes the raw scraped course data:
- strips weird unicode (non-breaking spaces, zero-width spaces)
- splits "title_raw" into course_code, title
- pulls credits out of the description if present
- drops entries with no usable description

Run locally: python clean_courses.py
Input:  courses.json (from scrape_courses.py)
Output: courses_clean.json
"""

import json
import re

INPUT_FILE = "courses.json"
OUTPUT_FILE = "courses_clean.json"


def normalize_whitespace(text):
    # Replace non-breaking space and zero-width space with normal space, collapse repeats
    text = text.replace("\u00a0", " ").replace("\u200b", "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def split_title(title_raw):
    """
    title_raw looks like: 'COMP SCI/MATH 240 — INTRODUCTION TO DISCRETE MATHEMATICS'
    Split into course_code ('COMP SCI/MATH 240') and title ('Introduction To Discrete Mathematics')
    """
    title_raw = normalize_whitespace(title_raw)
    if "—" in title_raw:
        code_part, name_part = title_raw.split("—", 1)
    elif "-" in title_raw:
        code_part, name_part = title_raw.split("-", 1)
    else:
        code_part, name_part = title_raw, ""
    return code_part.strip(), name_part.strip().title()


def main():
    with open(INPUT_FILE, encoding="utf-8") as f:
        raw = json.load(f)

    cleaned = []
    skipped = 0

    for c in raw:
        desc = normalize_whitespace(c.get("description", ""))
        if not desc:
            skipped += 1
            continue

        code, title = split_title(c.get("title_raw", ""))
        extra = normalize_whitespace(c.get("extra", ""))

        cleaned.append({
            "subject": c.get("subject", ""),
            "course_code": code,
            "title": title,
            "description": desc,
            "requisites": extra,
        })

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, indent=2)

    print(f"Cleaned {len(cleaned)} courses, skipped {skipped} with no description.")
    print(f"Saved to {OUTPUT_FILE}")

    # quick sanity check print
    print("\nSample:")
    print(json.dumps(cleaned[5], indent=2))


if __name__ == "__main__":
    main()