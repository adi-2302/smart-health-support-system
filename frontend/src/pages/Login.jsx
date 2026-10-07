import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../auth.jsx";
import { Logo } from "../components/Layout.jsx";
import { errorMessage } from "../util";

export default function Login() {
  const { login } = useAuth();
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setBusy(true); setError(null);
    try { await login(email.trim(), password); nav("/", { replace: true }); }
    catch (err) { setError(errorMessage(err)); setBusy(false); }
  }

  return (
    <div className="auth-wrap">
      <form className="card auth-card stack" onSubmit={submit}>
        <div>
          <Logo />
          <h1>Welcome back</h1>
          <p className="lede">A two-minute check-in, once a day.</p>
        </div>
        {error && <div className="notice error" role="alert">{error}</div>}
        <label className="field">Email
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoComplete="email" autoFocus />
        </label>
        <label className="field">Password
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required autoComplete="current-password" />
        </label>
        <button className="btn" disabled={busy}>{busy ? "Signing in…" : "Sign in"}</button>
        <p style={{ textAlign: "center", color: "var(--text-muted)" }}>New here? <Link to="/register">Create an account</Link></p>
      </form>
    </div>
  );
}
