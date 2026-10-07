import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api";
import { Spinner, ErrorBox } from "../components/Spinner.jsx";
import { errorMessage, groupQuestions } from "../util";

export default function Checkin() {
  const nav = useNavigate();
  const [questions, setQuestions] = useState(null);
  const [alreadyDone, setAlreadyDone] = useState(false);
  const [answers, setAnswers] = useState({});
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    Promise.all([api.questions(), api.today()])
      .then(([q, t]) => { setQuestions(q.questions); setAlreadyDone(t.completed); })
      .catch((e) => setError(errorMessage(e)));
  }, []);

  const groups = useMemo(() => (questions ? groupQuestions(questions) : []), [questions]);

  if (error && !questions) return <ErrorBox error={error} />;
  if (!questions) return <Spinner />;

  if (alreadyDone) {
    return (
      <div className="card empty">
        <h3>You've already checked in today</h3>
        <p style={{ marginBottom: 16 }}>One check-in per day keeps your trend meaningful. Come back tomorrow.</p>
        <div className="row" style={{ justifyContent: "center" }}>
          <Link className="btn" to="/result">View today's result</Link>
          <Link className="btn ghost" to="/">Dashboard</Link>
        </div>
      </div>
    );
  }

  const total = questions.length;
  const count = questions.filter((q) => answers[q.key] !== undefined).length;
  const firstMissing = questions.find((q) => answers[q.key] === undefined);

  async function submit() {
    if (firstMissing) {
      document.getElementById(`q-${firstMissing.key}`)?.scrollIntoView({ behavior: "smooth", block: "center" });
      setError(`Please answer: "${firstMissing.text}"`);
      return;
    }
    setBusy(true); setError(null);
    try { await api.submitCheckin(answers); nav("/result", { replace: true }); }
    catch (e) {
      if (e.status === 409) { nav("/result", { replace: true }); return; }
      setError(errorMessage(e)); setBusy(false);
    }
  }

  return (
    <div className="stack">
      <div className="page-head">
        <h1>Daily check-in</h1>
        <p>Think about today. There are no right or wrong answers.</p>
      </div>
      <div className="card">
        <div className="progress" role="progressbar" aria-valuemin={0} aria-valuemax={total} aria-valuenow={count} aria-label="Questions answered">
          <div style={{ width: `${(count / total) * 100}%` }} />
        </div>
        {groups.map((g) => (
          <section className="q-group" key={g.name}>
            <h2>{g.name}</h2>
            {g.items.map((q) => (
              <fieldset className="q" id={`q-${q.key}`} key={q.key} style={{ border: 0, margin: 0, padding: "18px 0" }}>
                <legend className="q-text" style={{ padding: 0 }}>{q.text}</legend>
                <div className="options">
                  {q.options.map((o) => (
                    <label className="opt" key={o.value}>
                      <input type="radio" name={q.key} value={o.value} checked={answers[q.key] === o.value}
                        onChange={() => { setAnswers((a) => ({ ...a, [q.key]: o.value })); setError(null); }} />
                      <span>{o.label}</span>
                    </label>
                  ))}
                </div>
              </fieldset>
            ))}
          </section>
        ))}
        <div className="sticky-bar">
          <span style={{ color: "var(--text-muted)" }}>{count} of {total} answered</span>
          <button className="btn" onClick={submit} disabled={busy}>{busy ? "Analysing…" : "See my result"}</button>
        </div>
        {error && <div className="notice error" role="alert" style={{ marginTop: 16 }}>{error}</div>}
      </div>
    </div>
  );
}
