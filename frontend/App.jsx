import React, { useMemo, useState } from "react";

const MODES = ["fast", "standard", "deep"];
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export default function App() {
  const [question, setQuestion] = useState(
    "What is the current state of multimodal agents in 2026?"
  );
  const [mode, setMode] = useState("deep");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [events, setEvents] = useState([]);
  const [report, setReport] = useState(null);

  const topClaims = useMemo(() => report?.claim_map?.slice(0, 6) || [], [report]);
  const topSources = useMemo(() => report?.sources?.slice(0, 8) || [], [report]);

  async function runResearch() {
    if (!question.trim()) return;

    setLoading(true);
    setError("");
    setEvents([]);
    setReport(null);

    try {
      const res = await fetch(`${API_BASE_URL}/research/live`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question,
          mode,
          max_results_per_source: mode === "deep" ? 6 : 4,
        }),
      });

      if (!res.ok) {
        const payload = await res.json().catch(() => ({}));
        throw new Error(payload?.detail || "Request failed");
      }

      const payload = await res.json();
      setEvents(payload.events || []);
      setReport(payload.report || null);
    } catch (err) {
      setError(err?.message || "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="shell">
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=IBM+Plex+Mono:wght@400;600&display=swap');

        :root {
          --bg-0: #050505;
          --bg-1: #0d0d0d;
          --ink-0: #f5f5f5;
          --ink-1: #d8d8d8;
          --ink-2: #9a9a9a;
          --line: rgba(255,255,255,0.16);
          --line-strong: rgba(255,255,255,0.34);
          --glass: rgba(255,255,255,0.04);
          --glass-2: rgba(255,255,255,0.08);
          --ok: #ffffff;
        }

        * {
          box-sizing: border-box;
        }

        body {
          margin: 0;
          background: var(--bg-0);
          color: var(--ink-0);
          font-family: 'Space Grotesk', sans-serif;
        }

        .shell {
          min-height: 100vh;
          background:
            radial-gradient(1400px 600px at 90% -10%, rgba(255,255,255,0.14), transparent 45%),
            radial-gradient(900px 500px at -20% 120%, rgba(255,255,255,0.1), transparent 50%),
            linear-gradient(180deg, #060606 0%, #0b0b0b 55%, #040404 100%);
          padding: 24px;
          position: relative;
          overflow: hidden;
        }

        .shell::before {
          content: "";
          position: fixed;
          inset: 0;
          pointer-events: none;
          background-image:
            linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px);
          background-size: 26px 26px;
          mask-image: radial-gradient(circle at center, black 48%, transparent 100%);
        }

        .container {
          max-width: 1200px;
          margin: 0 auto;
          display: grid;
          gap: 20px;
          animation: rise 620ms cubic-bezier(.2,.7,.2,1) both;
        }

        .hero {
          border: 1px solid var(--line);
          border-radius: 28px;
          background: linear-gradient(145deg, rgba(255,255,255,0.07), rgba(255,255,255,0.02));
          padding: 28px;
          position: relative;
          overflow: hidden;
        }

        .hero::after {
          content: "";
          position: absolute;
          inset: -30% -10% auto auto;
          width: 280px;
          height: 280px;
          border-radius: 999px;
          background: radial-gradient(circle, rgba(255,255,255,0.3), transparent 65%);
          filter: blur(24px);
          pointer-events: none;
        }

        .eyebrow {
          font-size: 12px;
          letter-spacing: 0.18em;
          text-transform: uppercase;
          color: var(--ink-2);
          margin-bottom: 8px;
          font-family: 'IBM Plex Mono', monospace;
        }

        .title {
          margin: 0;
          font-size: clamp(30px, 6vw, 64px);
          line-height: 0.96;
          letter-spacing: -0.02em;
        }

        .subtitle {
          margin: 14px 0 0;
          max-width: 900px;
          color: var(--ink-1);
          font-size: clamp(14px, 2vw, 19px);
          line-height: 1.45;
        }

        .grid {
          display: grid;
          grid-template-columns: 1.1fr 0.9fr;
          gap: 20px;
        }

        .panel {
          border: 1px solid var(--line);
          border-radius: 24px;
          background: var(--glass);
          backdrop-filter: blur(8px);
          padding: 18px;
        }

        .panel h3 {
          margin: 0 0 14px;
          font-size: 18px;
          letter-spacing: 0.02em;
        }

        .input {
          width: 100%;
          min-height: 110px;
          border-radius: 14px;
          border: 1px solid var(--line);
          background: #0b0b0b;
          color: var(--ink-0);
          padding: 14px;
          font-size: 15px;
          resize: vertical;
          outline: none;
          font-family: 'Space Grotesk', sans-serif;
        }

        .input:focus {
          border-color: var(--line-strong);
          box-shadow: 0 0 0 1px rgba(255,255,255,0.25) inset;
        }

        .row {
          margin-top: 14px;
          display: flex;
          gap: 10px;
          flex-wrap: wrap;
        }

        .chip {
          border: 1px solid var(--line);
          background: transparent;
          color: var(--ink-1);
          border-radius: 999px;
          padding: 8px 12px;
          font-family: 'IBM Plex Mono', monospace;
          font-size: 12px;
          text-transform: uppercase;
          letter-spacing: 0.06em;
          cursor: pointer;
          transition: 180ms ease;
        }

        .chip.active {
          background: #f2f2f2;
          color: #0c0c0c;
          border-color: #f2f2f2;
          transform: translateY(-1px);
        }

        .btn {
          border: 1px solid #fff;
          background: #fff;
          color: #080808;
          border-radius: 14px;
          padding: 11px 16px;
          font-weight: 700;
          letter-spacing: 0.02em;
          cursor: pointer;
          transition: 180ms ease;
        }

        .btn:hover {
          transform: translateY(-1px) scale(1.01);
          box-shadow: 0 8px 28px rgba(255,255,255,0.18);
        }

        .btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
          transform: none;
        }

        .mono {
          font-family: 'IBM Plex Mono', monospace;
          color: var(--ink-2);
          font-size: 12px;
          margin-top: 10px;
        }

        .events {
          max-height: 275px;
          overflow: auto;
          display: grid;
          gap: 8px;
          padding-right: 4px;
        }

        .event {
          border: 1px solid var(--line);
          background: rgba(255,255,255,0.02);
          border-radius: 12px;
          padding: 10px;
          animation: fadeIn 280ms ease both;
        }

        .event .meta {
          font-family: 'IBM Plex Mono', monospace;
          font-size: 11px;
          text-transform: uppercase;
          letter-spacing: 0.06em;
          color: var(--ink-2);
          margin-bottom: 4px;
        }

        .section {
          border: 1px solid var(--line);
          border-radius: 20px;
          background: var(--glass);
          padding: 16px;
        }

        .section h4 {
          margin: 0 0 12px;
          font-size: 16px;
        }

        .list {
          display: grid;
          gap: 10px;
        }

        .card {
          border: 1px solid var(--line);
          background: rgba(255,255,255,0.03);
          border-radius: 14px;
          padding: 12px;
          transition: 180ms ease;
        }

        .card:hover {
          border-color: var(--line-strong);
          background: rgba(255,255,255,0.05);
          transform: translateY(-1px);
        }

        .cardTitle {
          margin: 0 0 6px;
          font-size: 14px;
          color: #fff;
        }

        .cardText {
          margin: 0;
          color: var(--ink-1);
          font-size: 13px;
          line-height: 1.42;
        }

        .report {
          white-space: pre-wrap;
          margin: 0;
          color: var(--ink-1);
          font-size: 14px;
          line-height: 1.52;
        }

        .error {
          color: #ffffff;
          background: rgba(255,255,255,0.08);
          border: 1px solid rgba(255,255,255,0.2);
          border-radius: 10px;
          padding: 10px 12px;
          margin-top: 10px;
          font-family: 'IBM Plex Mono', monospace;
          font-size: 12px;
        }

        @keyframes rise {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }

        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(6px); }
          to { opacity: 1; transform: translateY(0); }
        }

        @media (max-width: 980px) {
          .grid {
            grid-template-columns: 1fr;
          }
          .shell {
            padding: 14px;
          }
          .hero {
            padding: 20px;
            border-radius: 20px;
          }
          .panel {
            border-radius: 18px;
          }
        }
      `}</style>

      <div className="container">
        <header className="hero">
          <div className="eyebrow">Unbelievable Mode</div>
          <h1 className="title">AI Research Lab</h1>
          <p className="subtitle">
            Monochrome command center for deep evidence retrieval, contradiction mapping,
            and confidence-graded claims from your backend pipeline.
          </p>
        </header>

        <div className="grid">
          <section className="panel">
            <h3>Launch Research</h3>
            <textarea
              className="input"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask a high-stakes research question..."
            />

            <div className="row">
              {MODES.map((m) => (
                <button
                  key={m}
                  className={`chip ${mode === m ? "active" : ""}`}
                  onClick={() => setMode(m)}
                  type="button"
                >
                  {m}
                </button>
              ))}
            </div>

            <div className="row">
              <button className="btn" onClick={runResearch} disabled={loading} type="button">
                {loading ? "Analyzing..." : "Run Autonomous Research"}
              </button>
            </div>

            <div className="mono">
              Endpoint: POST /research/live | Theme: Black + White | Status: {loading ? "BUSY" : "READY"}
            </div>

            {error && <div className="error">{error}</div>}
          </section>

          <section className="panel">
            <h3>Pipeline Events</h3>
            <div className="events">
              {events.length === 0 && (
                <div className="event">
                  <div className="meta">awaiting run</div>
                  <div>Events will appear here after you execute a query.</div>
                </div>
              )}
              {events.map((evt, idx) => (
                <div key={`${evt.timestamp_utc}-${idx}`} className="event">
                  <div className="meta">
                    {evt.stage} | {evt.status}
                  </div>
                  <div>{evt.message}</div>
                </div>
              ))}
            </div>
          </section>
        </div>

        <section className="section">
          <h4>Executive Brief</h4>
          <p className="report">{report?.executive_brief || "Run a query to generate the brief."}</p>
        </section>

        <div className="grid">
          <section className="section">
            <h4>Top Claims</h4>
            <div className="list">
              {topClaims.length === 0 && <div className="cardText">No claims yet.</div>}
              {topClaims.map((c) => (
                <article className="card" key={c.claim_id}>
                  <h5 className="cardTitle">{c.claim_id} | confidence {c.confidence}</h5>
                  <p className="cardText">{c.statement}</p>
                </article>
              ))}
            </div>
          </section>

          <section className="section">
            <h4>Top Sources</h4>
            <div className="list">
              {topSources.length === 0 && <div className="cardText">No sources yet.</div>}
              {topSources.map((s) => (
                <a className="card" key={s.id} href={s.url} target="_blank" rel="noreferrer">
                  <h5 className="cardTitle">[{s.source}] {s.title}</h5>
                  <p className="cardText">{s.summary || "No snippet available."}</p>
                </a>
              ))}
            </div>
          </section>
        </div>

        <section className="section">
          <h4>Technical Report</h4>
          <p className="report">{report?.technical_report || "Technical report will render here."}</p>
        </section>
      </div>
    </div>
  );
}
