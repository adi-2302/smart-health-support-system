"""
shap_explainer.py
Week 6: Explainable AI and Model Evaluation
Project: Smart Mental Health Support System for Students in Higher Education

Loads the trained XGBoost model (from Week 5) and generates SHAP explanations:
- Global feature importance (summary plot)
- Local per-prediction explanation (force plot + waterfall plot)

Uses SHAP's TreeExplainer, which computes exact Shapley values for tree-based
models (fast and mathematically exact, unlike model-agnostic KernelSHAP).
"""

import pickle
import pandas as pd
import numpy as np
import shap
import matplotlib.pyplot as plt

# ---- 1. Load the trained model and data ----
with open("xgboost_model.pkl", "rb") as f:
    model = pickle.load(f)

df = pd.read_csv("StressLevelDataset.csv")
X = df.drop(columns=["stress_level"])
y = df["stress_level"]

CLASS_NAMES = ["Low", "Medium", "High"]

# ---- 2. Build the SHAP TreeExplainer ----
explainer = shap.TreeExplainer(model)
shap_values = explainer(X)  # shap.Explanation object, shape (n_samples, n_features, n_classes)

print("SHAP values shape:", shap_values.shape)
print("Base values (per class):", explainer.expected_value)

# ---- 3. GLOBAL EXPLANATION: SHAP Summary Plot ----
# For multi-class, plot per-class summary + an aggregated bar chart across classes
plt.figure()
shap.summary_plot(shap_values, X, class_names=CLASS_NAMES, show=False)
plt.tight_layout()
plt.savefig("01_shap_summary_beeswarm.png", dpi=150, bbox_inches="tight")
plt.close()

plt.figure()
shap.summary_plot(shap_values, X, class_names=CLASS_NAMES, plot_type="bar", show=False)
plt.tight_layout()
plt.savefig("02_shap_summary_bar.png", dpi=150, bbox_inches="tight")
plt.close()

# ---- 4. LOCAL EXPLANATION: pick one real student's prediction to explain ----
sample_idx = 7  # arbitrary real row from the dataset
sample = X.iloc[[sample_idx]]
pred_class = model.predict(sample)[0]
pred_proba = model.predict_proba(sample)[0]

print(f"\nExplaining row {sample_idx}")
print("Actual stress_level:", y.iloc[sample_idx], "| Predicted:", pred_class, CLASS_NAMES[pred_class])
print("Predicted probabilities:", dict(zip(CLASS_NAMES, pred_proba.round(3))))

# Waterfall plot for the predicted class
plt.figure()
shap.plots.waterfall(shap_values[sample_idx, :, pred_class], show=False)
plt.tight_layout()
plt.savefig("03_shap_waterfall_sample.png", dpi=150, bbox_inches="tight")
plt.close()

# Force plot (matplotlib-rendered version, since interactive JS force plots
# don't export well to static reports)
plt.figure()
shap.plots.force(
    explainer.expected_value[pred_class],
    shap_values[sample_idx, :, pred_class].values,
    X.iloc[sample_idx],
    matplotlib=True,
    show=False,
)
plt.tight_layout()
plt.savefig("04_shap_force_sample.png", dpi=150, bbox_inches="tight")
plt.close()

# ---- 5. Save mean |SHAP value| per feature (for report table) ----
mean_abs_shap = np.abs(shap_values.values).mean(axis=(0, 2))  # average across samples and classes
importance_df = pd.DataFrame({
    "feature": X.columns,
    "mean_abs_shap": mean_abs_shap
}).sort_values("mean_abs_shap", ascending=False)
importance_df.to_csv("shap_feature_importance.csv", index=False)
print("\nTop 5 features by mean |SHAP value|:")
print(importance_df.head(5).to_string(index=False))

print("\nAll SHAP plots and the importance table have been saved.")
