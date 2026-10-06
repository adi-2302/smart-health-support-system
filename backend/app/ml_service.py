"""Model inference + SHAP explanations using the Week 5 XGBoost model and Week 6 TreeExplainer.

DESIGN NOTE (questionnaire -> model scale mapping)
The model was trained on StressLevelDataset.csv, whose features use different native
scales (e.g. anxiety_level 0-21, self_esteem 0-30, depression 0-27, most others 0-5,
social_support 0-3, blood_pressure 1-3). The daily check-in uses friendly 5-option
answers (0-4). Each answer is linearly rescaled onto the feature's native training range.
This is an approximation (documented as a limitation): the model has not been validated
on answers collected through this questionnaire, only on the original dataset's scales.
"""
import pickle
from functools import lru_cache

import numpy as np
import pandas as pd
import shap

from . import config

# Native (min, max) range of each feature in the training data (verified from the CSV).
NATIVE_RANGE = {
    "anxiety_level": (0, 21), "self_esteem": (0, 30), "mental_health_history": (0, 1),
    "depression": (0, 27), "headache": (0, 5), "blood_pressure": (1, 3),
    "sleep_quality": (0, 5), "breathing_problem": (0, 5), "noise_level": (0, 5),
    "living_conditions": (0, 5), "safety": (0, 5), "basic_needs": (0, 5),
    "academic_performance": (0, 5), "study_load": (0, 5), "teacher_student_relationship": (0, 5),
    "future_career_concerns": (0, 5), "social_support": (0, 3), "peer_pressure": (0, 5),
    "extracurricular_activities": (0, 5), "bullying": (0, 5),
}
ANSWER_MAX = 4  # questionnaire answers are 0-4 (blood_pressure is 1-3, passed through)

CLASS_NAMES = ["Low", "Medium", "High"]

# A feature only counts as a stress "driver" if its SHAP push toward High exceeds this
DRIVER_MIN_CONTRIBUTION = 0.15

FEATURE_LABELS = {
    "anxiety_level": "Anxiety", "self_esteem": "Self-esteem", "mental_health_history": "Mental health history",
    "depression": "Low mood", "headache": "Headaches", "blood_pressure": "Blood pressure",
    "sleep_quality": "Sleep quality", "breathing_problem": "Breathing difficulty", "noise_level": "Noise",
    "living_conditions": "Living conditions", "safety": "Sense of safety", "basic_needs": "Basic needs",
    "academic_performance": "Academic performance", "study_load": "Study load",
    "teacher_student_relationship": "Teacher relationship", "future_career_concerns": "Career worries",
    "social_support": "Social support", "peer_pressure": "Peer pressure",
    "extracurricular_activities": "Extracurricular load", "bullying": "Bullying",
}


@lru_cache(maxsize=1)
def _load():
    with open(config.MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    explainer = shap.TreeExplainer(model)
    feature_order = [str(c) for c in model.feature_names_in_]
    return model, explainer, feature_order


def to_model_features(answers: dict, mental_health_history: int) -> pd.DataFrame:
    """Rescale questionnaire answers onto the model's native feature scales."""
    _, _, order = _load()
    row = {}
    for feat in order:
        if feat == "mental_health_history":
            row[feat] = int(mental_health_history)
        elif feat == "blood_pressure":
            row[feat] = int(answers[feat])
        else:
            lo, hi = NATIVE_RANGE[feat]
            row[feat] = int(round(lo + (answers[feat] / ANSWER_MAX) * (hi - lo)))
    return pd.DataFrame([row], columns=order)


def _factors(shap_row: np.ndarray, X: pd.DataFrame, order: list[str], top_n: int) -> list[dict]:
    idx = np.argsort(-np.abs(shap_row))[:top_n]
    return [
        {
            "feature": order[i],
            "label": FEATURE_LABELS[order[i]],
            "value": int(X.iloc[0][order[i]]),
            "contribution": round(float(shap_row[i]), 4),
        }
        for i in idx
    ]


def predict_with_explanation(answers: dict, mental_health_history: int, top_n: int = 6) -> dict:
    model, explainer, order = _load()
    X = to_model_features(answers, mental_health_history)
    proba = model.predict_proba(X)[0]
    pred = int(np.argmax(proba))
    sv = explainer(X).values[0]  # shape (n_features, n_classes)

    # Probability-weighted 0-10 score: Low=0, Medium=0.5, High=1.0
    risk_score = float((proba[1] * 0.5 + proba[2] * 1.0) * 10)

    # Explanation of the predicted class (signed: + pushes toward this class)
    explanation = _factors(sv[:, pred], X, order, top_n)
    # Stress drivers: features pushing toward HIGH stress (used by the recommendation engine)
    high_sv = sv[:, 2]
    driver_idx = [i for i in np.argsort(-high_sv) if high_sv[i] > DRIVER_MIN_CONTRIBUTION][:3]
    drivers = [
        {"feature": order[i], "label": FEATURE_LABELS[order[i]],
         "value": int(X.iloc[0][order[i]]), "contribution": round(float(high_sv[i]), 4)}
        for i in driver_idx
    ]
    return {
        "predicted_class": pred,
        "predicted_label": CLASS_NAMES[pred],
        "confidence": round(float(proba[pred]), 4),
        "probabilities": {CLASS_NAMES[i]: round(float(p), 4) for i, p in enumerate(proba)},
        "risk_score": round(risk_score, 2),
        "explanation": explanation,
        "stress_drivers": drivers,
        "model_features": {k: int(v) for k, v in X.iloc[0].items()},
    }


def global_importance() -> list[dict]:
    """Static mean |SHAP| ranking saved in Week 6 (used by the dashboard)."""
    path = config.REPO_ROOT / "reports" / "shap_plots_v2" / "shap_feature_importance.csv"
    if not path.exists():
        return []
    df = pd.read_csv(path)
    return [{"feature": r.feature, "label": FEATURE_LABELS.get(r.feature, r.feature),
             "importance": round(float(r.mean_abs_shap), 4)} for r in df.itertuples()]
