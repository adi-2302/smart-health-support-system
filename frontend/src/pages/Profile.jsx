import { useAuth } from "../auth.jsx";
import ExamCard from "../components/ExamCard.jsx";
import { Link } from "react-router-dom";
import { Fragment } from "react";

export default function Profile() {
  const { user, exam } = useAuth();
  if (!user) return null;
  const rows = [
    ["Name", user.name], ["Email", user.email], ["Age", user.age ?? "—"], ["Gender", user.gender ?? "—"],
    ["Course", user.course ?? "—"], ["Year", user.year ?? "—"], ["Living situation", user.living_conditions ?? "—"],
    ["Mental health history", user.mental_health_history ? "Yes (used as a model input)" : "No"],
  ];
  return (
    <div className="stack">
      <div className="page-head"><h1>Profile</h1></div>
      <section className="card">
        <dl className="kv">{rows.map(([k, v]) => (<Fragment key={k}><dt>{k}</dt><dd>{v}</dd></Fragment>))}</dl>
      </section>
      <section className="card">
        <ExamCard exam={exam} />
        <p style={{ marginTop: 12 }}><Link to="/settings">Change exam date</Link></p>
      </section>
    </div>
  );
}
