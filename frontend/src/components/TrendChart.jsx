import { useEffect, useRef, useState } from "react";
import { shortDay, band } from "../util";

const COLORS = { low: "var(--sage)", mid: "var(--ochre)", high: "var(--rose)" };

// Line chart of daily risk (0-10). `entries`: [{date, risk_score}]
export default function TrendChart({ entries, height = 210 }) {
  // Draw at the real pixel width so text stays legible on phones.
  const ref = useRef(null);
  const [W, setW] = useState(640);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const measure = () => setW(Math.max(260, Math.round(el.getBoundingClientRect().width)));
    measure();
    if (typeof ResizeObserver === "undefined") return;
    const ro = new ResizeObserver(measure);
    ro.observe(el);
    return () => ro.disconnect();
  }, [entries?.length]);

  if (!entries?.length) return null;
  const H = height, padL = 32, padR = 16, padT = 14, padB = 30;
  const iw = W - padL - padR, ih = H - padT - padB;
  const x = (i) => padL + (entries.length === 1 ? iw / 2 : (i / (entries.length - 1)) * iw);
  const y = (v) => padT + ih - (Math.min(Math.max(v, 0), 10) / 10) * ih;
  const path = entries.map((e, i) => `${i ? "L" : "M"} ${x(i).toFixed(1)} ${y(e.risk_score).toFixed(1)}`).join(" ");
  const maxLabels = Math.max(2, Math.floor(iw / 48));
  const labelEvery = Math.max(1, Math.ceil(entries.length / maxLabels));
  const summary = entries.map((e) => `${e.date}: ${e.risk_score.toFixed(1)}`).join(", ");

  return (
    <svg ref={ref} className="chart" width="100%" height={H} viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`Daily risk score trend. ${summary}`}>
      <rect x={padL} y={y(10)} width={iw} height={y(6.5) - y(10)} fill="var(--rose-bg)" opacity=".55" />
      <rect x={padL} y={y(6.5)} width={iw} height={y(3.5) - y(6.5)} fill="var(--ochre-bg)" opacity=".55" />
      <rect x={padL} y={y(3.5)} width={iw} height={y(0) - y(3.5)} fill="var(--sage-bg)" opacity=".55" />
      {[0, 5, 10].map((t) => (
        <g key={t}>
          <line x1={padL} x2={W - padR} y1={y(t)} y2={y(t)} stroke="var(--line)" strokeDasharray="3 4" />
          <text x={padL - 8} y={y(t) + 4} textAnchor="end">{t}</text>
        </g>
      ))}
      {entries.length > 1 && <path d={path} fill="none" stroke="var(--accent)" strokeWidth="2.5" strokeLinejoin="round" strokeLinecap="round" />}
      {entries.map((e, i) => (
        <g key={e.date}>
          <circle cx={x(i)} cy={y(e.risk_score)} r="5" fill={COLORS[band(e.risk_score)]} stroke="var(--paper-raised)" strokeWidth="2">
            <title>{`${e.date} — ${e.risk_score.toFixed(1)} / 10`}</title>
          </circle>
          {i % labelEvery === 0 && <text x={x(i)} y={H - 10} textAnchor="middle">{shortDay(e.date)}</text>}
        </g>
      ))}
    </svg>
  );
}
