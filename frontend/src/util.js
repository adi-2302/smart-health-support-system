// Local calendar date as YYYY-MM-DD. toISOString() would use UTC and shift the day
// for users east of UTC (e.g. IST) in the early morning.
export function localDate(d = new Date()) {
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${d.getFullYear()}-${m}-${day}`;
}

export function parseLocal(iso) {
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(y, m - 1, d);
}

export function shortDay(iso) {
  return parseLocal(iso).toLocaleDateString(undefined, { weekday: "short" });
}

export function prettyDate(iso) {
  return parseLocal(iso).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" });
}

// Risk score is 0-10. Bands match how the label colours are used across the app.
export function band(score) {
  if (score == null) return "none";
  if (score < 3.5) return "low";
  if (score < 6.5) return "mid";
  return "high";
}

export const BAND_LABEL = { low: "Low", mid: "Medium", high: "High", none: "—" };

export function labelBand(label) {
  return { Low: "low", Medium: "mid", High: "high" }[label] ?? "none";
}

export function signed(n, digits = 1) {
  if (n == null) return "—";
  const v = Number(n).toFixed(digits);
  return n > 0 ? `+${v}` : v;
}

export function examText(exam) {
  if (!exam || exam.days_remaining == null) return null;
  const d = exam.days_remaining;
  if (d < 0) return `${exam.exam_label || "Exam"} was ${-d} day${d === -1 ? "" : "s"} ago`;
  if (d === 0) return `${exam.exam_label || "Exam"} is today`;
  return `${d} day${d === 1 ? "" : "s"} to ${exam.exam_label || "your exam"}`;
}

// Group the questionnaire by its `group` field, preserving order.
export function groupQuestions(questions) {
  const groups = [];
  for (const q of questions) {
    let g = groups.find((x) => x.name === q.group);
    if (!g) groups.push((g = { name: q.group, items: [] }));
    g.items.push(q);
  }
  return groups;
}

export function errorMessage(err) {
  return err?.message || "Something went wrong. Please try again.";
}
