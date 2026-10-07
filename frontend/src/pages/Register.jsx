import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../auth.jsx";
import { Logo } from "../components/Layout.jsx";
import { errorMessage, localDate } from "../util";

export default function Register() {
  const { register } = useAuth();
  const nav = useNavigate();
  const [f, setF] = useState({
    name: "", email: "", password: "", age: "", gender: "", course: "", year: "", living_conditions: "",
    mental_health_history: false, exam_date: "", exam_label: "",
  });
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setF({ ...f, [k]: e.target.type === "checkbox" ? e.target.checked : e.target.value });

  async function submit(e) {
    e.preventDefault();
    setBusy(true); setError(null);
    const payload = {
      ...f, name: f.name.trim(), email: f.email.trim(),
      age: f.age === "" ? null : Number(f.age),
      gender: f.gender || null, course: f.course.trim() || null, year: f.year || null,
      living_conditions: f.living_conditions || null, exam_label: f.exam_label.trim() || null,
    };
    try { await register(payload); nav("/", { replace: true }); }
    catch (err) { setError(errorMessage(err)); setBusy(false); }
  }

  return (
    <div className="auth-wrap">
      <form className="card auth-card wide stack" onSubmit={submit}>
        <div>
          <Logo />
          <h1>Create your account</h1>
          <p className="lede">Your exam date lets MindTrack count down automatically — you'll never be asked for it again.</p>
        </div>
        {error && <div className="notice error" role="alert">{error}</div>}
        <div className="form-grid">
          <label className="field">Name<input type="text" value={f.name} onChange={set("name")} required autoComplete="name" /></label>
          <label className="field">Email<input type="email" value={f.email} onChange={set("email")} required autoComplete="email" /></label>
          <label className="field">Password (8+ characters)<input type="password" value={f.password} onChange={set("password")} required minLength={8} autoComplete="new-password" /></label>
          <label className="field">Age<input type="number" min="15" max="60" value={f.age} onChange={set("age")} /></label>
          <label className="field">Gender
            <select value={f.gender} onChange={set("gender")}>
              <option value="">Prefer not to say</option><option>Female</option><option>Male</option><option>Non-binary</option><option>Other</option>
            </select>
          </label>
          <label className="field">Course<input type="text" value={f.course} onChange={set("course")} placeholder="e.g. B.Tech CSE" /></label>
          <label className="field">Year
            <select value={f.year} onChange={set("year")}>
              <option value="">—</option><option>1st</option><option>2nd</option><option>3rd</option><option>4th</option><option>Postgraduate</option>
            </select>
          </label>
          <label className="field">Living situation
            <select value={f.living_conditions} onChange={set("living_conditions")}>
              <option value="">—</option><option>Hostel</option><option>Home</option><option>Rented room</option>
            </select>
          </label>
          <label className="field">Next exam date<input type="date" value={f.exam_date} onChange={set("exam_date")} min={localDate()} required /></label>
          <label className="field">Exam name (optional)<input type="text" value={f.exam_label} onChange={set("exam_label")} placeholder="e.g. Semester 7 finals" /></label>
        </div>
        <label className="check">
          <input type="checkbox" checked={f.mental_health_history} onChange={set("mental_health_history")} />
          I have a history of mental health concerns (used as one model input; never shown to anyone else)
        </label>
        <button className="btn" disabled={busy}>{busy ? "Creating account…" : "Create account"}</button>
        <p style={{ textAlign: "center", color: "var(--text-muted)" }}>Already registered? <Link to="/login">Sign in</Link></p>
      </form>
    </div>
  );
}
