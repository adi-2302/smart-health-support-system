// SHAP contributions toward the predicted class. Positive = pushed toward it, negative = pulled away.
// `mode="signed"` centres bars on zero; `mode="magnitude"` plots non-negative importances.
export default function DriverBars({ items, mode = "signed", valueKey = "contribution" }) {
  if (!items?.length) return null;
  const max = Math.max(...items.map((i) => Math.abs(i[valueKey])), 0.0001);
  return (
    <div className="bars">
      {items.map((it) => {
        const v = it[valueKey];
        const w = (Math.abs(v) / max) * (mode === "signed" ? 50 : 100);
        const style = mode === "signed"
          ? { width: `${w}%`, left: v >= 0 ? "50%" : `${50 - w}%` }
          : { width: `${w}%`, left: 0 };
        return (
          <div className="bar-row" key={it.feature}>
            <span>{it.label}</span>
            <div className="bar-track" aria-hidden="true">
              {mode === "signed" && <div className="bar-axis" />}
              <div className={`bar-fill ${mode === "signed" ? (v >= 0 ? "up" : "down") : "neutral"}`} style={style} />
            </div>
            <span className="bar-val">{mode === "signed" && v > 0 ? "+" : ""}{v.toFixed(2)}</span>
          </div>
        );
      })}
    </div>
  );
}
