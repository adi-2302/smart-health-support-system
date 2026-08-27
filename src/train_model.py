"""
train_model.py
Phase 3 / Week 5: Machine Learning Model Development
Project: Smart Mental Health Support System for Students in Higher Education

Trains and compares Logistic Regression, Decision Tree, Random Forest, and XGBoost
on StressLevelDataset.csv using 5-fold stratified cross-validation and hyperparameter
tuning (GridSearchCV). Selects the best model based on cross-validated F1-score.

Imports the shared preprocessing pipeline from data_preprocessing.py so training-time
and (later) inference-time preprocessing stay identical.
"""

import time
import json
import pandas as pd
import numpy as np

from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier

from sklearn.model_selection import GridSearchCV
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, roc_auc_score
)
from sklearn.preprocessing import label_binarize

import sys
sys.path.append('.')
from data_preprocessing import run_preprocessing_pipeline, get_cv_splitter


# ---------------------------------------------------------------------------
# 1. Hyperparameter grids per model (kept small/sensible for a 1,100-row dataset
#    so GridSearchCV finishes quickly without overfitting to noise)
# ---------------------------------------------------------------------------

MODEL_GRIDS = {
    "Logistic Regression": {
        "estimator": LogisticRegression(max_iter=1000, random_state=42),
        "params": {
            "C": [0.01, 0.1, 1, 10],
            "solver": ["lbfgs"],
        }
    },
    "Decision Tree": {
        "estimator": DecisionTreeClassifier(random_state=42),
        "params": {
            "max_depth": [3, 5, 7, 10, None],
            "min_samples_split": [2, 5, 10],
        }
    },
    "Random Forest": {
        "estimator": RandomForestClassifier(random_state=42),
        "params": {
            "n_estimators": [100, 200, 300],
            "max_depth": [5, 10, None],
        }
    },
    "XGBoost": {
        "estimator": XGBClassifier(
            random_state=42, eval_metric="mlogloss"
        ),
        "params": {
            "n_estimators": [100, 200, 300],
            "max_depth": [3, 5, 7],
            "learning_rate": [0.01, 0.1, 0.2],
        }
    },
}


# ---------------------------------------------------------------------------
# 2. Train + tune + evaluate one model
# ---------------------------------------------------------------------------

def train_and_evaluate(name, config, X_train, X_test, y_train, y_test, cv):
    start = time.time()

    grid = GridSearchCV(
        estimator=config["estimator"],
        param_grid=config["params"],
        cv=cv,
        scoring="f1_weighted",
        n_jobs=-1,
    )
    grid.fit(X_train, y_train)
    training_time = time.time() - start

    best_model = grid.best_estimator_
    y_pred = best_model.predict(X_test)
    y_proba = best_model.predict_proba(X_test)

    # Multi-class ROC-AUC (one-vs-rest)
    y_test_bin = label_binarize(y_test, classes=[0, 1, 2])
    try:
        roc_auc = roc_auc_score(y_test_bin, y_proba, multi_class="ovr", average="weighted")
    except ValueError:
        roc_auc = None

    metrics = {
        "Model": name,
        "Best Params": grid.best_params_,
        "Accuracy": accuracy_score(y_test, y_pred),
        "Precision": precision_score(y_test, y_pred, average="weighted"),
        "Recall": recall_score(y_test, y_pred, average="weighted"),
        "F1 Score": f1_score(y_test, y_pred, average="weighted"),
        "ROC-AUC": roc_auc,
        "CV F1 (mean)": grid.best_score_,
        "Training Time (s)": round(training_time, 2),
    }
    cm = confusion_matrix(y_test, y_pred)

    return metrics, cm, best_model


# ---------------------------------------------------------------------------
# 3. Run full comparison across all 4 models
# ---------------------------------------------------------------------------

def run_model_comparison(raw_csv_path: str):
    pipeline = run_preprocessing_pipeline(raw_csv_path)
    X_train, X_test = pipeline["X_train"], pipeline["X_test"]
    y_train, y_test = pipeline["y_train"], pipeline["y_test"]
    cv = pipeline["cv_splitter"]

    results = []
    confusion_matrices = {}
    trained_models = {}

    for name, config in MODEL_GRIDS.items():
        print(f"Training {name}...")
        metrics, cm, model = train_and_evaluate(
            name, config, X_train, X_test, y_train, y_test, cv
        )
        results.append(metrics)
        confusion_matrices[name] = cm
        trained_models[name] = model
        print(f"  -> Accuracy={metrics['Accuracy']:.4f}  F1={metrics['F1 Score']:.4f}  "
              f"Time={metrics['Training Time (s)']}s")

    results_df = pd.DataFrame(results).sort_values("F1 Score", ascending=False).reset_index(drop=True)
    best_model_name = results_df.iloc[0]["Model"]

    return {
        "results_df": results_df,
        "confusion_matrices": confusion_matrices,
        "trained_models": trained_models,
        "best_model_name": best_model_name,
        "best_model": trained_models[best_model_name],
        "X_test": X_test,
        "y_test": y_test,
    }


if __name__ == "__main__":
    output = run_model_comparison("data/raw/StressLevelDataset.csv")
    print("\n=== FINAL COMPARISON TABLE ===")
    print(output["results_df"].to_string(index=False))
    print(f"\nBest model selected: {output['best_model_name']}")
