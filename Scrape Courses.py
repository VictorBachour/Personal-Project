"""
scrape_courses.py

Scrapes course data from guide.wisc.edu for one or more subjects.
Run this locally (not in a sandboxed environment) since it needs real internet access.

Usage:
    python scrape_courses.py
"""

import requests
from bs4 import BeautifulSoup
import json
import time

# Add/remove subject codes here. Each maps to a guide.wisc.edu URL slug.
SUBJECTS = {
    "COMP SCI": "comp_sci",
    "STAT": "stat",
    "MATH": "math",
}

BASE_URL = "https://guide.wisc.edu/courses/{slug}/"
HEADERS = {"User-Agent": "Mozilla/5.0 (student project; course data collection)"}


def scrape_subject(subject_name, slug):
    url = BASE_URL.format(slug=slug)
    print(f"Fetching {url} ...")
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # NOTE: guide.wisc.edu appears to run on a catalog platform (Acalog-style).
    # Common class names for this type of site are "courseblock", "courseblocktitle",
    # and "courseblockdesc". If this doesn't match what you see when you run it,
    # print(soup.prettify()[:3000]) to inspect the real structure, and send me
    # a snippet — we'll adjust the selectors together.
    course_blocks = soup.find_all("div", class_="courseblock")

    if not course_blocks:
        print(f"  No 'courseblock' divs found for {subject_name}. "
              f"Dumping first 2000 chars of HTML for inspection:")
        print(resp.text[:2000])
        return []

    courses = []
    for block in course_blocks:
        title_tag = block.find(class_="courseblocktitle")
        desc_tag = block.find(class_="courseblockdesc")
        extra_tag = block.find(class_="courseblockextra") or block.find(class_="cb-extra")

        title_text = title_tag.get_text(" ", strip=True) if title_tag else ""
        desc_text = desc_tag.get_text(" ", strip=True) if desc_tag else ""
        extra_text = extra_tag.get_text(" ", strip=True) if extra_tag else ""

        courses.append({
            "subject": subject_name,
            "title_raw": title_text,
            "description": desc_text,
            "extra": extra_text,
        })

    print(f"  Found {len(courses)} courses for {subject_name}")
    return courses


def main():
    all_courses = []
    for subject_name, slug in SUBJECTS.items():
        courses = scrape_subject(subject_name, slug)
        all_courses.extend(courses)
        time.sleep(1)  # be polite to the server

    with open("courses.json", "w", encoding="utf-8") as f:
        json.dump(all_courses, f, indent=2)

    print(f"\nSaved {len(all_courses)} total courses to courses.json")


if __name__ == "__main__":
    main()