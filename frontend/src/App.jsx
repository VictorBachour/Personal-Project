import { useState } from "react";

const API_URL = `${import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000"}/ask`;

const SAMPLE_QUESTIONS = [
  "What courses teach me about databases?",
  "I want to learn machine learning, what should I take?",
  "Is there a course on discrete math?",
];

export default function App() {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  async function handleAsk(q) {
    const finalQuestion = q ?? question;
    if (!finalQuestion.trim()) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: finalQuestion, top_k: 5 }),
      });

      if (!res.ok) {
        throw new Error(`Server responded with ${res.status}`);
      }

      const data = await res.json();
      setResult(data);
    } catch (err) {
      setError(
        "Couldn't reach the advisor. Make sure the backend is running at " +
          API_URL
      );
    } finally {
      setLoading(false);
    }
  }

  function handleSubmit(e) {
    e.preventDefault();
    handleAsk();
  }

  return (
    <div className="page">
      <div className="crest" aria-hidden="true">W</div>

      <header className="header">
        <p className="eyebrow">Comp Sci · Stat · Math</p>
        <h1>Course Advisor</h1>
        <p className="subhead">
          Ask a question in plain English. Answers are grounded in real UW–Madison
          course descriptions — not guessed.
        </p>
      </header>

      <form className="ask-form" onSubmit={handleSubmit}>
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="e.g. What courses teach me about databases?"
          aria-label="Ask a question about UW-Madison courses"
        />
        <button type="submit" disabled={loading}>
          {loading ? "Thinking…" : "Ask"}
        </button>
      </form>

      <div className="samples">
        {SAMPLE_QUESTIONS.map((q) => (
          <button
            key={q}
            className="sample-chip"
            onClick={() => {
              setQuestion(q);
              handleAsk(q);
            }}
            type="button"
          >
            {q}
          </button>
        ))}
      </div>

      {error && <div className="error">{error}</div>}

      {result && (
        <div className="result">
          <p className="answer">{result.answer}</p>

          <div className="meta">
            Answered in {result.response_time_ms}ms
          </div>

          <div className="sources">
            <p className="sources-label">Sources</p>
            {result.sources.map((s) => (
              <div className="source-card" key={s.course_code}>
                <div className="source-code">{s.course_code}</div>
                <div className="source-title">{s.title}</div>
                <p className="source-desc">{s.description}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}