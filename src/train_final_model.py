"""
train_final_model.py
Retrains XGBoost with hyperparameters selected for PROBABILITY QUALITY (CV log-loss),
because the app's risk score, trend tracking and early-warning logic all depend on
predicted probabilities, not just on the argmax class.

Why: the Week 5 grid search optimised weighted F1 and picked learning_rate=0.01 with 100 trees.
That gives the right classes (87.3% test accuracy) but near-uniform probabilities (mean max
probability 0.67, risk scores squeezed into ~2-8 of 0-10). Selection here uses 5-fold stratified
CV on the TRAINING split only; the test split is evaluated once at the end.
Saves to models/xgboost_model_v2.pkl (the Week 5 model is kept untouched).
"""
import pickle
import pandas as pd
from sklearn.model_selection import GridSearchCV, StratifiedKFold, train_test_split
from sklearn.metrics import accuracy_score, f1_score, log_loss, confusion_matrix
from xgboost import XGBClassifier

df = pd.read_csv("data/raw/StressLevelDataset.csv")
X, y = df.drop(columns=["stress_level"]), df["stress_level"]
# Same split as Week 5 (80/20, stratified, random_state=42) so results are comparable
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

grid = GridSearchCV(
    XGBClassifier(random_state=42, eval_metric="mlogloss"),
    {"learning_rate": [0.01, 0.03, 0.05, 0.1, 0.2], "n_estimators": [100, 200], "max_depth": [3, 5]},
    scoring="neg_log_loss",
    cv=StratifiedKFold(5, shuffle=True, random_state=42),
    n_jobs=-1,
).fit(Xtr, ytr)

best = grid.best_estimator_
proba = best.predict_proba(Xte)
pred = proba.argmax(1)
print("Selected by CV log-loss:", grid.best_params_)
print(f"CV log-loss (train only): {-grid.best_score_:.3f}")
print(f"TEST  accuracy={accuracy_score(yte, pred):.4f}  F1={f1_score(yte, pred, average='weighted'):.4f}  log-loss={log_loss(yte, proba):.3f}")
print("Mean max-probability:", round(float(proba.max(1).mean()), 2))
print("Confusion matrix:\n", confusion_matrix(yte, pred))

with open("models/xgboost_model_v2.pkl", "wb") as f:
    pickle.dump(best, f)
print("Saved models/xgboost_model_v2.pkl")
