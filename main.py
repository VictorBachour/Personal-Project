"""
main.py

FastAPI wrapper around the RAG pipeline built in generate.py / search.py.
Exposes:
  GET  /health          - simple liveness check
  POST /ask             - takes a question, returns an answer + sources

Run locally: uvicorn main:app --reload
Then visit http://127.0.0.1:8000/docs for interactive API docs (FastAPI
generates this automatically).
"""

import os
import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from generate import answer_question

app = FastAPI(
    title="UW Course Advisor API",
    description="RAG-based Q&A over UW-Madison course descriptions (COMP SCI, STAT, MATH)",
    version="1.0.0",
)

# Allows your React frontend (running on a different port/domain) to call this API.
# Reads allowed origins from an env var so local dev and production can differ
# without changing code. Set ALLOWED_ORIGINS on Render once you have your
# Vercel URL, e.g.: ALLOWED_ORIGINS=https://your-app.vercel.app
origins_env = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173")
allowed_origins = [o.strip() for o in origins_env.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=500)
    top_k: int = Field(default=5, ge=1, le=10)


class SourceCourse(BaseModel):
    course_code: str
    title: str
    description: str


class AskResponse(BaseModel):
    answer: str
    sources: list[SourceCourse]
    response_time_ms: int


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    start = time.time()

    try:
        answer, results = answer_question(request.question, top_k=request.top_k)
    except Exception as e:
        # Don't leak internal error details (API keys, stack traces) to the client.
        raise HTTPException(status_code=500, detail="Something went wrong processing your question.") from e

    elapsed_ms = int((time.time() - start) * 1000)

    sources = [
        SourceCourse(
            course_code=r["course_code"],
            title=r["title"],
            description=r["description"],
        )
        for r in results
    ]

    return AskResponse(answer=answer, sources=sources, response_time_ms=elapsed_ms)