import { NavLink, Link, Outlet } from "react-router-dom";
import { useAuth } from "../auth.jsx";

export function Logo() {
  return (
    <svg className="brand-mark" viewBox="0 0 32 32" aria-hidden="true">
      <circle cx="16" cy="16" r="14" fill="var(--sage)" />
      <path d="M9 17c3-6 11-6 14 0" stroke="#fff" strokeWidth="2.5" fill="none" strokeLinecap="round" />
    </svg>
  );
}

const LINKS = [
  ["/", "Dashboard", true],
  ["/checkin", "Check-in"],
  ["/weekly", "Weekly report"],
  ["/insights", "Insights"],
  ["/profile", "Profile"],
  ["/settings", "Settings"],
];

export default function Layout() {
  const { logout } = useAuth();
  return (
    <div className="shell">
      <header className="topbar">
        <Link to="/" className="brand"><Logo />MindTrack</Link>
        <nav className="nav" aria-label="Main">
          {LINKS.map(([to, label, end]) => (
            <NavLink key={to} to={to} end={end} className={({ isActive }) => (isActive ? "active" : "")}>{label}</NavLink>
          ))}
        </nav>
        <button className="btn ghost small" onClick={logout}>Sign out</button>
      </header>
      <main className="page"><Outlet /></main>
    </div>
  );
}
