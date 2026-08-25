# UW Course Advisor

A full-stack RAG (Retrieval-Augmented Generation) application that answers natural-language questions about UW-Madison courses, grounded in real course catalog data — not general LLM knowledge.

**Live demo:** https://uw-madison-course-api.vercel.app/
**API docs:** https://uw-course-advisor-api.onrender.com/docs

> Note: the backend is hosted on Render's free tier, which spins down after 15 minutes of inactivity. The first request after idle time may take 30–60 seconds to respond while the server wakes up.

---

## What it does

Ask a plain-English question like *"What courses teach me about databases?"* or *"I want to learn machine learning, what should I take?"*, and the app retrieves the most relevant real UW-Madison courses and generates a grounded, cited answer — rather than hallucinating a response from general training data.

If a question has no good answer in the dataset (e.g. *"What courses teach me French?"*), the system is designed to say so honestly instead of forcing an unrelated course to fit.

---

## Architecture

```
guide.wisc.edu  →  scraper  →  cleaning  →  embeddings  →  vector search  →  LLM answer  →  API  →  React UI
```

1. **Scraping** (`scrape_courses.py`) — pulls course data (title, description, requisites) directly from UW-Madison's public course guide for three departments: Computer Sciences, Statistics, and Mathematics.
2. **Cleaning** (`clean_courses.py`) — normalizes unicode artifacts from the source HTML, splits course codes from titles, and drops any incomplete entries. 384 of 385 scraped courses passed cleaning.
3. **Embedding** (`build_embeddings.py`) — each course is treated as a single chunk (course descriptions are already short and self-contained, so no further splitting was needed) and embedded using OpenAI's `text-embedding-3-small`.
4. **Retrieval** (`search.py`) — a user's question is embedded the same way, then compared against all course embeddings using cosine similarity to find the top-k most relevant courses.
5. **Generation** (`generate.py`) — the retrieved courses are passed to `gpt-4o-mini` along with the original question, with a system prompt that explicitly restricts the model to only use the provided context and to cite course codes, and to say so honestly if nothing relevant was retrieved.
6. **API** (`main.py`) — a FastAPI service exposing `/ask` and `/health`, deployed on Render.
7. **Frontend** (`frontend/`) — a React + Vite single-page app, deployed on Vercel, styled around UW-Madison's cardinal red.

---

## Evaluation

Rather than assume the system worked, I built a 16-question hand-written eval set (`eval_suite.py`) covering three categories: direct matches, conceptually-phrased questions, and deliberately out-of-scope questions.

| Metric | Result |
|---|---|
| Retrieval accuracy | 100% (12/12 answerable questions) |
| Refusal accuracy | 100% (4/4 out-of-scope questions correctly declined) |

**Worth noting honestly:** the first run of this eval scored 83% retrieval accuracy, with two "failures" on questions about neural networks and probability/statistics. On inspection, these weren't retrieval bugs — the system had actually returned *more specific, more correct* courses (e.g. a dedicated Artificial Neural Networks course, and an advanced Probability and Statistical Theory course) than my initial hand-written ground truth anticipated, since I hadn't yet reviewed the full scraped catalog when I wrote the expected answers. I manually verified the actual courses, updated the eval set, and re-ran it. This is included here because it reflects a more realistic evaluation process than a suspiciously perfect first-pass score.

---

## Known limitations

- Only three departments are covered (Computer Sciences, Statistics, Mathematics) — this was a deliberate scope decision to keep the project achievable in a short timeframe, not a technical limitation of the pipeline.
- UW's cross-listed courses (e.g. a course jointly listed under two departments) appear as separate entries in the scraped data, since that's how the source site structures them. This occasionally surfaces the "same" course twice in results.
- No conversation memory — each question is answered independently.
- Backend cold-start delay on Render's free tier (see note above).

## What I'd improve with more time

- Expand scraping to the full course catalog rather than three departments
- Deduplicate cross-listed courses at the cleaning stage
- Swap the flat cosine-similarity search for a proper vector database (e.g. pgvector) to support a larger catalog efficiently
- Add conversation memory for follow-up questions

---

## Tech stack

**Backend:** Python, FastAPI, OpenAI API (embeddings + chat completion), NumPy
**Frontend:** React, Vite
**Deployment:** Render (backend), Vercel (frontend)
**Data:** Scraped from guide.wisc.edu

---

## Running locally

**Backend:**
```bash
pip install -r requirements.txt
# add your OPENAI_API_KEY to a .env file
python scrape_courses.py
python clean_courses.py
python build_embeddings.py
uvicorn main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```
