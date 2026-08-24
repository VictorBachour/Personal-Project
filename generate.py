"""
generate.py

The "generation" half of RAG:
  1. Uses search.py to retrieve the top-k most relevant courses for a question
  2. Feeds those courses + the question to an LLM as context
  3. Returns a natural-language answer that cites specific course codes

Run: python generate.py
(interactive prompt, same as search.py, but now returns a real answer)
"""

import os
from openai import OpenAI
from dotenv import load_dotenv
from search import search  # reuse the retrieval function we already built

load_dotenv()

CHAT_MODEL = "gpt-4o-mini"

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def build_context(results):
    """
    Format retrieved courses into a text block the LLM can read.
    Keeping this simple and explicit makes it easy to debug what
    the model actually saw when it generates a bad answer.
    """
    blocks = []
    for r in results:
        blocks.append(
            f"{r['course_code']} — {r['title']}\n{r['description']}"
        )
    return "\n\n".join(blocks)


SYSTEM_PROMPT = """You are a helpful academic advisor assistant for UW-Madison.
You answer student questions about courses using ONLY the course information
provided in the context below. 

Rules:
- Only recommend courses that appear in the provided context.
- Always cite the course code (e.g. "COMP SCI 564") when mentioning a course.
- If the provided context doesn't actually answer the question well, say so
  honestly instead of forcing a recommendation.
- Keep answers concise — a few sentences, not an essay.
"""


def answer_question(question, top_k=5):
    results = search(question, top_k=top_k)
    context = build_context(results)

    user_message = f"""Context (retrieved courses):
{context}

Student question: {question}"""

    response = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.3,
    )

    answer = response.choices[0].message.content
    return answer, results


if __name__ == "__main__":
    print("Course advisor — type a question, or 'quit' to exit.\n")
    while True:
        question = input("Question: ").strip()
        if question.lower() in ("quit", "exit"):
            break
        if not question:
            continue

        answer, results = answer_question(question)
        print("\nAnswer:")
        print(answer)
        print("\n(sources used):")
        for r in results:
            print(f"  - {r['course_code']}: {r['title']}")
        print()