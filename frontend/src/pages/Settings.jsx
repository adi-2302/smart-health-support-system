import { useState } from "react";
import { api } from "../api";
import { useAuth } from "../auth.jsx";
import { getTheme, setTheme } from "../theme.js";
import { errorMessage, localDate } from "../util";

export default function Settings() {
  const { exam, setExam, logout } = useAuth();
  const [date, setDate] = useState(exam?.exam_date || "");
  const [label, setLabel] = useState(exam?.exam_label || "");
  const [theme, setT] = useState(getTheme());
  const [msg, setMsg] = useState(null);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  async function saveExam(e) {
    e.preventDefault();
    setBusy(true); setMsg(null); setError(null);
    try {
      const r = await api.updateExam({ exam_date: date, exam_label: label.trim() || null });
      setExam(r.exam); setMsg("Exam date updated. Your countdown and suggestions now use it.");
    } catch (err) { setError(errorMessage(err)); }
    setBusy(false);
  }

  return (
    <div className="stack">
      <div className="page-head"><h1>Settings</h1></div>

      <form className="card stack" onSubmit={saveExam}>
        <div><h2>Exam date</h2><p className="sub">Used for the automatic countdown and exam-aware suggestions.</p></div>
        {msg && <div className="notice info" role="status">{msg}</div>}
        {error && <div className="notice error" role="alert">{error}</div>}
        <div className="form-grid">
          <label className="field">Exam date<input type="date" value={date} onChange={(e) => setDate(e.target.value)} min={localDate()} required /></label>
          <label className="field">Exam name<input type="text" value={label} onChange={(e) => setLabel(e.target.value)} /></label>
        </div>
        <div><button className="btn" disabled={busy}>{busy ? "Saving…" : "Save exam date"}</button></div>
      </form>

      <section className="card stack">
        <div><h2>Appearance</h2></div>
        <div className="seg" role="group" aria-label="Theme">
          {["system", "light", "dark"].map((m) => (
            <button key={m} aria-pressed={theme === m} onClick={() => { setTheme(m); setT(m); }}>{m[0].toUpperCase() + m.slice(1)}</button>
          ))}
        </div>
      </section>

      <section className="card stack">
        <div><h2>Account</h2></div>
        <div><button className="btn ghost" onClick={logout}>Sign out</button></div>
      </section>
    </div>
  );
}
