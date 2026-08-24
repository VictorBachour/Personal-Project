"""
search.py

Given a natural-language question, finds the most relevant courses by:
  1. Embedding the question with the same model used for the courses
  2. Comparing it against every course embedding using cosine similarity
  3. Returning the top-k most similar courses

Run: python search.py
(has a small test block at the bottom so you can try questions interactively)
"""

import json
import os
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

EMBEDDINGS_FILE = "embeddings.npz"
EMBEDDING_MODEL = "text-embedding-3-small"

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def load_index():
    data = np.load(EMBEDDINGS_FILE, allow_pickle=True)
    embeddings = data["embeddings"]
    courses = json.loads(str(data["courses"]))
    return embeddings, courses


def embed_query(text):
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=[text])
    return np.array(response.data[0].embedding, dtype=np.float32)


def cosine_similarity(query_vec, all_vecs):
    """
    Standard cosine similarity between one query vector and a matrix of vectors.
    Returns a similarity score per row (per course).
    """
    query_norm = query_vec / np.linalg.norm(query_vec)
    all_norms = all_vecs / np.linalg.norm(all_vecs, axis=1, keepdims=True)
    return all_norms @ query_norm


def search(question, top_k=5):
    embeddings, courses = load_index()
    query_vec = embed_query(question)
    scores = cosine_similarity(query_vec, embeddings)

    # get indices of the top_k highest scores, sorted descending
    top_indices = np.argsort(scores)[::-1][:top_k]

    results = []
    for idx in top_indices:
        course = courses[idx]
        results.append({
            "score": float(scores[idx]),
            "course_code": course["course_code"],
            "title": course["title"],
            "description": course["description"],
        })
    return results


if __name__ == "__main__":
    print("Course search — type a question, or 'quit' to exit.\n")
    while True:
        question = input("Question: ").strip()
        if question.lower() in ("quit", "exit"):
            break
        if not question:
            continue

        results = search(question, top_k=5)
        print()
        for r in results:
            print(f"  [{r['score']:.3f}] {r['course_code']} — {r['title']}")
            print(f"          {r['description'][:150]}...")
        print()