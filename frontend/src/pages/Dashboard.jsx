import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../auth.jsx";
import RiskGauge from "../components/RiskGauge.jsx";
import TrendChart from "../components/TrendChart.jsx";
import ExamCard from "../components/ExamCard.jsx";
import EarlyWarning from "../components/EarlyWarning.jsx";
import Recommendations from "../components/Recommendations.jsx";
import { Spinner, ErrorBox } from "../components/Spinner.jsx";
import { band, errorMessage, labelBand, signed } from "../util";

export default function Dashboard() {
  const { user } = useAuth();
  const [today, setToday] = useState(null);
  const [hist, setHist] = useState(null);
  const [error, setError] = useState(null);

  const load = useCallback(() => {
    setError(null);
    Promise.all([api.today(), api.history(14)])
      .then(([t, h]) => { setToday(t); setHist(h.entries); })
      .catch((e) => setError(errorMessage(e)));
  }, []);
  useEffect(load, [load]);

  if (error) return <ErrorBox error={error} onRetry={load} />;
  if (!today || !hist) return <Spinner />;

  const first = user?.name?.split(" ")[0] || "there";
  const done = today.completed;
  const p = today.prediction;

  return (
    <div className="stack">
      <div className="page-head">
        <h1>Hello, {first}</h1>
        <p>{done ? "You've checked in today. Here's where things stand." : "How are you doing today? A short check-in takes about two minutes."}</p>
      </div>

      {done && <EarlyWarning warning={today.early_warning} />}

      <div className="grid two">
        <section className="card">
          <span className="eyebrow">Today</span>
          {done ? (
            <>
              <RiskGauge score={p.risk_score} />
              <div className="row spread" style={{ marginTop: 8 }}>
                <span className={`badge ${labelBand(p.predicted_label)}`}>Most likely: {p.predicted_label}</span>
                <span style={{ color: "var(--text-muted)", fontSize: ".9rem" }}>
                  vs last check-in: {today.comparison.change == null ? "first one" : signed(today.comparison.change)}
                </span>
              </div>
              <div className="row" style={{ marginTop: 16 }}>
                <Link className="btn small" to="/result">See why</Link>
              </div>
            </>
          ) : (
            <div className="empty">
              <h3>Not checked in yet</h3>
              <p style={{ marginBottom: 16 }}>19 quick multiple-choice questions.</p>
              <Link className="btn" to="/checkin">Start today's check-in</Link>
            </div>
          )}
        </section>

        <section className="card stack">
          <ExamCard exam={today.exam} />
          {!today.exam?.exam_date && <p className="sub">No exam date set. <Link to="/settings">Add one</Link>.</p>}
        </section>
      </div>

      <section className="card">
        <h2>Last 14 days</h2>
        <p className="sub">Daily risk score (0–10). Shaded bands: low, medium, high.</p>
        {hist.length ? <TrendChart entries={hist} /> : (
          <div className="empty"><h3>No history yet</h3><p>Your trend appears after your first check-in.</p></div>
        )}
        {hist.length > 0 && (
          <div className="legend" style={{ marginTop: 8 }}>
            {["low", "mid", "high"].map((b) => (
              <span key={b}><span className="dot" style={{ background: { low: "var(--sage)", mid: "var(--ochre)", high: "var(--rose)" }[b] }} />{{ low: "Low", mid: "Medium", high: "High" }[b]}</span>
            ))}
          </div>
        )}
      </section>

      {done && (
        <section className="card">
          <h2>Suggestions for today</h2>
          <p className="sub">Based on your answers, what's driving your stress, and your exam timeline.</p>
          <Recommendations items={today.recommendations} />
        </section>
      )}
      <p className="disclaimer">MindTrack is a self-reflection tool, not a medical or diagnostic service.</p>
    </div>
  );
}
