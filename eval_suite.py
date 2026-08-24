"""
eval_suite.py

A hand-written evaluation set for the course RAG system.

Each test case has:
  - a question
  - a list of course codes that WOULD be a correct/acceptable retrieval
    (sometimes more than one course reasonably answers a question)
  - a flag "should_have_match": False for questions that intentionally
    have no good answer in this dataset (tests that the system doesn't
    force a bad match)

Scoring approach:
  - Retrieval accuracy: for each question, did at least one of the
    expected courses appear in the top-k retrieved results?
  - Refusal accuracy: for "should_have_match: False" questions, did the
    generated answer correctly decline instead of forcing a match?

This is intentionally simple (hit/miss, not fuzzy grading) so the numbers
are easy to explain and defend if someone asks how you evaluated the system.

Run: python eval_suite.py
"""

from search import search
from generate import answer_question

TOP_K = 5

EVAL_CASES = [
    # --- Clear, direct matches ---
    {
        "question": "What course teaches discrete math?",
        "expected_any": ["COMP SCI/MATH 240", "MATH/COMP SCI 240"],
        "should_have_match": True,
    },
    {
        "question": "I want an introductory machine learning course.",
        "expected_any": ["STAT 451", "COMP SCI/E C E 760"],
        "should_have_match": True,
    },
    {
        "question": "What's a good first programming course for beginners?",
        "expected_any": ["COMP SCI 200", "COMP SCI/L I S 102"],
        "should_have_match": True,
    },
    {
        "question": "Is there a course on database management systems?",
        "expected_any": ["COMP SCI 564"],
        "should_have_match": True,
    },
    {
        "question": "What course covers Java programming specifically?",
        "expected_any": ["COMP SCI 303"],
        "should_have_match": True,
    },

    # --- Slightly indirect / conceptual phrasing ---
    {
        "question": "I want to understand how neural networks work.",
        "expected_any": ["COMP SCI/E C E 760", "COMP SCI 761", "COMP SCI/E C E 761",
                         "COMP SCI/E C E/M E 539"],
        "should_have_match": True,
    },
    {
        "question": "What should I take if I'm interested in web development?",
        "expected_any": ["COMP SCI 272"],
        "should_have_match": True,
    },
    {
        "question": "Any courses about probability and statistics for data science?",
        "expected_any": ["STAT 240", "STAT 301", "MATH 535", "MATH/STAT 409", "STAT/MATH 409"],
        "should_have_match": True,
    },
    {
        "question": "I'm interested in how computers are physically built.",
        "expected_any": ["COMP SCI/E C E 252"],
        "should_have_match": True,
    },
    {
        "question": "What course would teach me about big datasets and distributed storage?",
        "expected_any": ["COMP SCI 544"],
        "should_have_match": True,
    },

    # --- Edge cases: things that sound tech-adjacent but aren't in this dataset ---
    {
        "question": "What courses teach me French?",
        "expected_any": [],
        "should_have_match": False,
    },
    {
        "question": "Where can I learn to be a better person?",
        "expected_any": [],
        "should_have_match": False,
    },
    {
        "question": "Is there a course on marketing strategy?",
        "expected_any": [],
        "should_have_match": False,
    },
    {
        "question": "What's the best course for learning how to cook?",
        "expected_any": [],
        "should_have_match": False,
    },

    # --- Ambiguous but should still surface something reasonable ---
    {
        "question": "I like math but I'm not sure what to take next.",
        "expected_any": ["MATH 112", "MATH 113", "MATH 114", "MATH 141", "MATH 491"],
        "should_have_match": True,
    },
    {
        "question": "What's a graduate-level theory course in machine learning?",
        "expected_any": ["STAT/COMP SCI/E C E 861", "COMP SCI/E C E/STAT 861"],
        "should_have_match": True,
    },
]


def run_retrieval_eval():
    print("=" * 60)
    print("RETRIEVAL EVAL (does the right course appear in top-k?)")
    print("=" * 60)

    hits = 0
    total_scored = 0

    for case in EVAL_CASES:
        if not case["should_have_match"]:
            continue  # retrieval accuracy only applies to answerable questions
        total_scored += 1

        results = search(case["question"], top_k=TOP_K)
        retrieved_codes = [r["course_code"] for r in results]

        hit = any(code in retrieved_codes for code in case["expected_any"])
        hits += hit

        status = "PASS" if hit else "FAIL"
        print(f"[{status}] {case['question']}")
        if not hit:
            print(f"       expected one of: {case['expected_any']}")
            print(f"       got: {retrieved_codes}")

    accuracy = hits / total_scored if total_scored else 0
    print(f"\nRetrieval accuracy: {hits}/{total_scored} ({accuracy:.0%})")
    return accuracy


def run_refusal_eval():
    print("\n" + "=" * 60)
    print("REFUSAL EVAL (does it correctly decline out-of-scope questions?)")
    print("=" * 60)

    correct = 0
    total = 0

    refusal_signals = ["don't", "does not", "no course", "not contain",
                       "not available", "sorry", "unfortunately"]

    for case in EVAL_CASES:
        if case["should_have_match"]:
            continue
        total += 1

        answer, _ = answer_question(case["question"], top_k=TOP_K)
        declined = any(signal in answer.lower() for signal in refusal_signals)
        correct += declined

        status = "PASS" if declined else "FAIL"
        print(f"[{status}] {case['question']}")
        if not declined:
            print(f"       answer: {answer[:200]}")

    accuracy = correct / total if total else 0
    print(f"\nRefusal accuracy: {correct}/{total} ({accuracy:.0%})")
    return accuracy


if __name__ == "__main__":
    retrieval_acc = run_retrieval_eval()
    refusal_acc = run_refusal_eval()

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Retrieval accuracy: {retrieval_acc:.0%}")
    print(f"Refusal accuracy:   {refusal_acc:.0%}")