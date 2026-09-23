"""
train_model_synthetic.py
Model comparison on the synthetic reduced-feature dataset.

Two evaluations, both reported honestly:
1. Raw 10-class (1-10) target -- as originally specified. Cannot use proper
   stratified CV because several classes have <5 samples (class 1 has just 1).
2. Binned 3-class target (Low/Medium/High) -- added for a fair, apples-to-apples
   comparison against StressLevelDataset.csv's 3-class 87.3% XGBoost result.
"""

import time
import pandas as pd
import numpy as np

from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier

from sklearn.model_selection import GridSearchCV, StratifiedKFold, KFold, train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

df = pd.read_csv("data/raw/synthetic_student_stress_dataset.csv")
X = df.drop(columns=["stress_level"])
y_raw = df["stress_level"]

MODEL_GRIDS = {
    "Logistic Regression": {
        "estimator": LogisticRegression(max_iter=1000, random_state=42),
        "params": {"C": [0.01, 0.1, 1, 10], "solver": ["lbfgs"]},
    },
    "Decision Tree": {
        "estimator": DecisionTreeClassifier(random_state=42),
        "params": {"max_depth": [3, 5, 7, 10, None], "min_samples_split": [2, 5, 10]},
    },
    "Random Forest": {
        "estimator": RandomForestClassifier(random_state=42),
        "params": {"n_estimators": [100, 200, 300], "max_depth": [5, 10, None]},
    },
    "XGBoost": {
        "estimator": XGBClassifier(random_state=42, eval_metric="mlogloss"),
        "params": {"n_estimators": [100, 200, 300], "max_depth": [3, 5, 7], "learning_rate": [0.01, 0.1, 0.2]},
    },
}


def run_comparison(X, y, cv, label):
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42,
        stratify=y if cv.__class__.__name__ == "StratifiedKFold" else None
    )
    results = []
    for name, config in MODEL_GRIDS.items():
        start = time.time()
        grid = GridSearchCV(config["estimator"], config["params"], cv=cv, scoring="f1_weighted", n_jobs=-1)
        grid.fit(X_train, y_train)
        elapsed = time.time() - start
        y_pred = grid.best_estimator_.predict(X_test)
        results.append({
            "Model": name,
            "Accuracy": accuracy_score(y_test, y_pred),
            "Precision": precision_score(y_test, y_pred, average="weighted", zero_division=0),
            "Recall": recall_score(y_test, y_pred, average="weighted", zero_division=0),
            "F1 Score": f1_score(y_test, y_pred, average="weighted", zero_division=0),
            "CV F1 (mean)": grid.best_score_,
            "Training Time (s)": round(elapsed, 2),
        })
        print(f"  [{label}] {name}: Acc={results[-1]['Accuracy']:.4f}  F1={results[-1]['F1 Score']:.4f}")
    return pd.DataFrame(results).sort_values("F1 Score", ascending=False).reset_index(drop=True)


print("=== Evaluation 1: RAW 10-class (1-10) ===")
print("Using plain KFold (not stratified) -- several classes have too few samples to stratify.\n")
cv_raw = KFold(n_splits=5, shuffle=True, random_state=42)
y_raw_shifted = y_raw - 1  # XGBoost requires 0-indexed integer classes
results_raw = run_comparison(X, y_raw_shifted, cv_raw, "raw-10class")

print("\n=== Evaluation 2: BINNED 3-class (Low 1-4 / Medium 5-7 / High 8-10) ===")
print("For fair comparison against StressLevelDataset.csv's 3-class result.\n")
y_binned_labels = pd.cut(y_raw, bins=[0, 4, 7, 10], labels=["Low", "Medium", "High"])
label_map = {"Low": 0, "Medium": 1, "High": 2}
y_binned = y_binned_labels.map(label_map)
cv_binned = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
results_binned = run_comparison(X, y_binned, cv_binned, "binned-3class")

print("\n\n=== RAW 10-CLASS RESULTS ===")
print(results_raw.to_string(index=False))
print("\n=== BINNED 3-CLASS RESULTS ===")
print(results_binned.to_string(index=False))

results_raw.to_csv("model_comparison_synthetic_raw10.csv", index=False)
results_binned.to_csv("model_comparison_synthetic_binned3.csv", index=False)
