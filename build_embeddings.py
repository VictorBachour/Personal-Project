"""
build_embeddings.py

Turns courses_clean.json into a searchable vector index:
  1. Formats each course into a single text chunk (course = natural chunk boundary)
  2. Calls OpenAI's embedding API for each chunk
  3. Saves embeddings + metadata to embeddings.npz for fast local search later

Cost note: text-embedding-3-small costs $0.02 per 1M tokens. For ~384 short
course descriptions, this run will cost well under $0.01 total — your $5
in credits covers this many times over.

Requires: pip install openai numpy python-dotenv
Run: python build_embeddings.py
"""

import json
import os
import time
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

INPUT_FILE = "courses_clean.json"
OUTPUT_FILE = "embeddings.npz"
EMBEDDING_MODEL = "text-embedding-3-small"

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def course_to_text(course):
    """
    Combine course fields into one text blob for embedding.
    This is the 'chunk' — for course data, one course = one chunk,
    since descriptions are already short and self-contained.
    """
    parts = [
        f"{course['course_code']}: {course['title']}",
        course["description"],
    ]
    if course.get("requisites"):
        parts.append(course["requisites"])
    return " | ".join(parts)


def embed_batch(texts, batch_size=100):
    """
    OpenAI's embedding endpoint accepts multiple inputs per call, which is
    much faster and cheaper than one call per course. Batch to stay safely
    under request size limits.
    """
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        print(f"  Embedding batch {i}-{i+len(batch)} of {len(texts)}...")
        response = client.embeddings.create(model=EMBEDDING_MODEL, input=batch)
        batch_embeddings = [item.embedding for item in response.data]
        all_embeddings.extend(batch_embeddings)
        time.sleep(0.2)  # small buffer to stay comfortably under rate limits
    return all_embeddings


def main():
    with open(INPUT_FILE, encoding="utf-8") as f:
        courses = json.load(f)

    print(f"Loaded {len(courses)} courses.")

    texts = [course_to_text(c) for c in courses]
    print("Sample chunk text:")
    print(" ", texts[0])
    print()

    print("Generating embeddings...")
    embeddings = embed_batch(texts)
    embeddings_array = np.array(embeddings, dtype=np.float32)

    print(f"Got embeddings with shape {embeddings_array.shape}")

    # Save embeddings + the original course metadata together so we can
    # look up which course each embedding belongs to at search time.
    np.savez(
        OUTPUT_FILE,
        embeddings=embeddings_array,
        courses=json.dumps(courses),
    )

    print(f"Saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()