"""
shap_explainer_v2.py  (Week 6 follow-up: explains the deployed model xgboost_model_v2.json)

Generates SHAP explanations with TreeExplainer (exact Shapley values for tree models):
  - global importance: beeswarm (High-stress class) + bar (all classes)
  - local explanation: waterfall + force plot for one real student record
  - shap_feature_importance.csv: mean |SHAP| per feature (served by the API at /insights/global)

Run from the repo root:  python src/shap_explainer_v2.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
from xgboost import XGBClassifier

MODEL_FILE = "models/xgboost_model_v2.json"
DATA_FILE = "data/raw/StressLevelDataset.csv"
OUT_DIR = Path("reports/shap_plots_v2")
SAMPLE_IDX = 7
CLASS_NAMES = ["Low", "Medium", "High"]

OUT_DIR.mkdir(parents=True, exist_ok=True)
model = XGBClassifier()
model.load_model(MODEL_FILE)
df = pd.read_csv(DATA_FILE)
X, y = df.drop(columns=["stress_level"]), df["stress_level"]

explainer = shap.TreeExplainer(model)
sv = explainer(X)  # (n_samples, n_features, n_classes)
print("SHAP values shape:", sv.shape)

# Global: beeswarm for the High-stress class (multi-class beeswarm needs one class selected)
plt.figure(); shap.summary_plot(sv[:, :, 2], X, show=False)
plt.title("SHAP summary: contribution to 'High stress' prediction", fontsize=11)
plt.tight_layout(); plt.savefig(OUT_DIR / "01_shap_summary_beeswarm.png", dpi=150, bbox_inches="tight"); plt.close()

# Global: bar chart across all three classes
plt.figure(); shap.summary_plot(sv, X, class_names=CLASS_NAMES, plot_type="bar", show=False)
plt.tight_layout(); plt.savefig(OUT_DIR / "02_shap_summary_bar.png", dpi=150, bbox_inches="tight"); plt.close()

# Local: one real student
sample = X.iloc[[SAMPLE_IDX]]
proba = model.predict_proba(sample)[0]
pred = int(np.argmax(proba))
print(f"Row {SAMPLE_IDX}: actual={CLASS_NAMES[y.iloc[SAMPLE_IDX]]}  predicted={CLASS_NAMES[pred]}  "
      f"probs={dict(zip(CLASS_NAMES, proba.round(3)))}")

plt.figure(); shap.plots.waterfall(sv[SAMPLE_IDX, :, pred], show=False)
plt.tight_layout(); plt.savefig(OUT_DIR / "03_shap_waterfall_sample.png", dpi=150, bbox_inches="tight"); plt.close()

plt.figure()
shap.plots.force(explainer.expected_value[pred], sv[SAMPLE_IDX, :, pred].values, X.iloc[SAMPLE_IDX],
                 matplotlib=True, show=False)
plt.tight_layout(); plt.savefig(OUT_DIR / "04_shap_force_sample.png", dpi=150, bbox_inches="tight"); plt.close()

# Importance table (mean |SHAP| averaged over samples and classes)
imp = pd.DataFrame({"feature": X.columns, "mean_abs_shap": np.abs(sv.values).mean(axis=(0, 2))})
imp = imp.sort_values("mean_abs_shap", ascending=False)
imp.to_csv(OUT_DIR / "shap_feature_importance.csv", index=False)
print(imp.head(6).to_string(index=False))
