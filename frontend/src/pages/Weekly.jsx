import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import TrendChart from "../components/TrendChart.jsx";
import DriverBars from "../components/DriverBars.jsx";
import EarlyWarning from "../components/EarlyWarning.jsx";
import Recommendations from "../components/Recommendations.jsx";
import ExamCard from "../components/ExamCard.jsx";
import { Spinner, ErrorBox } from "../components/Spinner.jsx";
import { band, BAND_LABEL, errorMessage, localDate, parseLocal, prettyDate, signed } from "../util";

const TREND_TEXT = {
  rising: "Higher than last week", falling: "Lower than last week", stable: "About the same as last week",
  no_previous_week: "No earlier week to compare yet", insufficient_data: "Not enough data to compare yet",
};

export default function Weekly() {
  const [end, setEnd] = useState(localDate());
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    setData(null); setError(null);
    api.weekly(end).then(setData).catch((e) => setError(errorMessage(e)));
  }, [end]);

  function shift(days) {
    const d = parseLocal(end); d.setDate(d.getDate() + days);
    const next = localDate(d);
    if (next <= localDate()) setEnd(next);
  }

  return (
    <div className="stack">
      <div className="page-head row spread">
        <div>
          <h1>Weekly report</h1>
          {data?.window && <p>{prettyDate(data.window.start)} – {prettyDate(data.window.end)}</p>}
        </div>
        <div className="row">
          <button className="btn ghost small" onClick={() => shift(-7)} aria-label="Previous week">← Earlier</button>
          <button className="btn ghost small" onClick={() => shift(7)} disabled={end >= localDate()} aria-label="Next week">Later →</button>
        </div>
      </div>

      {error && <ErrorBox error={error} />}
      {!data && !error && <Spinner />}

      {data && !data.has_data && (
        <div className="card empty">
          <h3>No check-ins this week</h3>
          <p style={{ marginBottom: 16 }}>{data.message}</p>
          <Link className="btn" to="/checkin">Do a check-in</Link>
        </div>
      )}

      {data?.has_data && <ReportBody r={data} />}
    </div>
  );
}

function ReportBody({ r }) {
  const s = r.summary, v = r.vs_previous_week;
  const avgBand = band(s.average_risk);
  return (
    <>
      <EarlyWarning warning={r.early_warning} />
      <section className="card">
        <div className="stats">
          <div className="stat"><span className="eyebrow">Average risk</span><span className="value">{s.average_risk.toFixed(1)}</span><span className={`badge ${avgBand}`} style={{ justifySelf: "start" }}>{BAND_LABEL[avgBand]}</span></div>
          <div className="stat"><span className="eyebrow">Check-ins</span><span className="value">{s.checkins}<small style={{ fontSize: "1rem", color: "var(--text-muted)" }}> / 7</small></span><span className="label">days this week</span></div>
          <div className="stat"><span className="eyebrow">Hardest day</span><span className="value">{s.highest_day.risk_score.toFixed(1)}</span><span className="label">{prettyDate(s.highest_day.date)}</span></div>
          <div className="stat"><span className="eyebrow">Calmest day</span><span className="value">{s.lowest_day.risk_score.toFixed(1)}</span><span className="label">{prettyDate(s.lowest_day.date)}</span></div>
        </div>
      </section>

      <section className="card">
        <h2>Day by day</h2>
        <p className="sub">{TREND_TEXT[v.trend] || "No earlier week to compare yet"}{v.change != null && <> · {signed(v.change)} vs last week's average of {v.previous_average.toFixed(1)}</>}</p>
        <TrendChart entries={r.daily} />
      </section>

      <div className="grid two">
        <section className="card">
          <h2>What drove your stress</h2>
          <p className="sub">Stress drivers summed across the week.</p>
          {r.contributing_factors.length
            ? <DriverBars items={r.contributing_factors} mode="magnitude" valueKey="total_contribution" />
            : <p style={{ color: "var(--text-muted)" }}>No single factor stood out this week — a good sign.</p>}
        </section>
        <section className="card stack">
          <ExamCard exam={r.exam} />
        </section>
      </div>

      <section className="card">
        <h2>Suggestions for next week</h2>
        <Recommendations items={r.recommendations} />
      </section>
    </>
  );
}
