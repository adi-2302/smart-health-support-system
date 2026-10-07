import { band, BAND_LABEL } from "../util";

const COLORS = { low: "var(--sage)", mid: "var(--ochre)", high: "var(--rose)", none: "var(--line)" };

// Half-circle gauge for the 0-10 risk score.
export default function RiskGauge({ score }) {
  const b = band(score);
  const frac = score == null ? 0 : Math.min(Math.max(score / 10, 0), 1);
  const r = 90, cx = 110, cy = 105;
  const pt = (f) => {
    const a = Math.PI * (1 - f);
    return [cx + r * Math.cos(a), cy - r * Math.sin(a)];
  };
  const [sx, sy] = pt(0);
  const [ex, ey] = pt(1);
  const [vx, vy] = pt(frac);
  return (
    <div className="gauge" role="img" aria-label={`Risk score ${score?.toFixed(1)} out of 10, ${BAND_LABEL[b]}`}>
      <svg viewBox="0 0 220 125">
        <path d={`M ${sx} ${sy} A ${r} ${r} 0 0 1 ${ex} ${ey}`} stroke="var(--paper-sunken)" strokeWidth="16" fill="none" strokeLinecap="round" />
        {frac > 0 && (
          <path d={`M ${sx} ${sy} A ${r} ${r} 0 0 1 ${vx} ${vy}`} stroke={COLORS[b]} strokeWidth="16" fill="none" strokeLinecap="round" />
        )}
      </svg>
      <div style={{ marginTop: -64 }}>
        <div className="score">{score == null ? "—" : score.toFixed(1)}</div>
        <div className="of">out of 10</div>
      </div>
    </div>
  );
}
