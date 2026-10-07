import { useEffect, useState } from "react";
import { api } from "../api";
import DriverBars from "../components/DriverBars.jsx";
import { Spinner, ErrorBox } from "../components/Spinner.jsx";
import { errorMessage } from "../util";

export default function Insights() {
  const [features, setFeatures] = useState(null);
  const [error, setError] = useState(null);
  useEffect(() => { api.globalInsights().then((r) => setFeatures(r.features)).catch((e) => setError(errorMessage(e))); }, []);

  if (error) return <ErrorBox error={error} />;
  if (!features) return <Spinner />;

  return (
    <div className="stack">
      <div className="page-head">
        <h1>What the model looks at</h1>
        <p>Overall, which questions influence predictions the most across everyone in the training data.</p>
      </div>
      <section className="card">
        <h2>Global feature importance</h2>
        <p className="sub">Mean absolute SHAP value — larger means the model relies on it more.</p>
        <DriverBars items={features.slice(0, 12)} mode="magnitude" valueKey="importance" />
      </section>
      <section className="card">
        <h2>How to read this</h2>
        <p style={{ color: "var(--ink-soft)" }}>
          These are patterns the model learned from a public student-stress dataset. They describe statistical association, not cause and effect,
          and your own result page shows what mattered for <em>you</em> today. Your answers are scaled to the dataset's ranges, so treat
          scores as a guide for reflection rather than a clinical measurement.
        </p>
      </section>
    </div>
  );
}
