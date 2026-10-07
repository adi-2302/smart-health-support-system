import { useEffect, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { api } from "../api";
import RiskGauge from "../components/RiskGauge.jsx";
import DriverBars from "../components/DriverBars.jsx";
import EarlyWarning from "../components/EarlyWarning.jsx";
import Recommendations from "../components/Recommendations.jsx";
import ExamCard from "../components/ExamCard.jsx";
import { Spinner, ErrorBox } from "../components/Spinner.jsx";
import { errorMessage, labelBand, prettyDate, signed } from "../util";

export default function Result() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  useEffect(() => { api.today().then(setData).catch((e) => setError(errorMessage(e))); }, []);

  if (error) return <ErrorBox error={error} />;
  if (!data) return <Spinner />;
  if (!data.completed) return <Navigate to="/checkin" replace />;

  const p = data.prediction;
  const probs = ["Low", "Medium", "High"].map((k) => ({ k, v: p.probabilities?.[k] ?? 0 }));

  return (
    <div className="stack">
      <div className="page-head">
        <span className="eyebrow">{prettyDate(data.date)}</span>
        <h1>Your result</h1>
      </div>

      <EarlyWarning warning={data.early_warning} />

      <div className="grid two">
        <section className="card">
          <RiskGauge score={p.risk_score} />
          <div className="row spread" style={{ marginTop: 8 }}>
            <span className={`badge ${labelBand(p.predicted_label)}`}>Most likely: {p.predicted_label}</span>
            <span style={{ color: "var(--text-muted)", fontSize: ".9rem" }}>model confidence {(p.confidence * 100).toFixed(0)}%</span>
          </div>
        </section>
        <section className="card stack">
          <div className="stats">
            <div className="stat">
              <span className="eyebrow">Since last check-in</span>
              <span className="value">{data.comparison.change == null ? "—" : signed(data.comparison.change)}</span>
              <span className="label">{data.comparison.previous_risk_score == null ? "This is your first check-in" : `was ${data.comparison.previous_risk_score.toFixed(1)}`}</span>
            </div>
            <ExamCard exam={data.exam} />
          </div>
          <div>
            <span className="eyebrow">How sure is the model?</span>
            <div className="bars" style={{ marginTop: 8 }}>
              {probs.map(({ k, v }) => (
                <div className="bar-row" key={k} style={{ gridTemplateColumns: "70px 1fr 48px" }}>
                  <span>{k}</span>
                  <div className="bar-track" aria-hidden="true"><div className={`bar-fill neutral`} style={{ left: 0, width: `${v * 100}%`, background: { Low: "var(--sage)", Medium: "var(--ochre)", High: "var(--rose)" }[k] }} /></div>
                  <span className="bar-val">{(v * 100).toFixed(0)}%</span>
                </div>
              ))}
            </div>
          </div>
        </section>
      </div>

      <section className="card">
        <h2>Why this result?</h2>
        <p className="sub">The factors that moved today's prediction most (SHAP). Red pushed it toward <strong>{p.predicted_label}</strong>; green pulled it away.</p>
        <DriverBars items={p.explanation} />
        <div className="legend" style={{ marginTop: 14 }}>
          <span><span className="dot" style={{ background: "var(--rose)" }} />Pushes toward {p.predicted_label}</span>
          <span><span className="dot" style={{ background: "var(--sage)" }} />Pulls away</span>
        </div>
        {p.stress_drivers?.length > 0 && (
          <p style={{ marginTop: 16 }}>
            <strong>Main stress drivers today:</strong> {p.stress_drivers.map((d) => d.label).join(", ")}.
          </p>
        )}
      </section>

      <section className="card">
        <h2>What might help</h2>
        <p className="sub">Tailored to your answers, your exam timeline, and your recent trend.</p>
        <Recommendations items={data.recommendations} />
      </section>

      <div className="row">
        <Link className="btn" to="/">Back to dashboard</Link>
        <Link className="btn ghost" to="/weekly">Weekly report</Link>
      </div>
      <p className="disclaimer">Predictions come from a statistical model and can be wrong. This is not a diagnosis. If you're struggling, please reach out to a counsellor or someone you trust.</p>
    </div>
  );
}
