import { examText, prettyDate } from "../util";

export default function ExamCard({ exam }) {
  const text = examText(exam);
  if (!text) return null;
  return (
    <div className="stat">
      <span className="eyebrow">Exam countdown</span>
      <span className="value">{exam.days_remaining >= 0 ? exam.days_remaining : "—"}<small style={{ fontSize: "1rem", color: "var(--text-muted)" }}> {exam.days_remaining >= 0 ? (exam.days_remaining === 1 ? "day" : "days") : ""}</small></span>
      <span className="label">{text} · {prettyDate(exam.exam_date)}</span>
      {exam.in_exam_period && <span className="badge mid" style={{ justifySelf: "start", marginTop: 4 }}>Exam period</span>}
    </div>
  );
}
