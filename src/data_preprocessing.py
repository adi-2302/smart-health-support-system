"""
data_preprocessing.py
Phase 2: Preprocessing & Feature Engineering
Project: Smart Mental Health Support System for Students in Higher Education

This module is imported by BOTH:
  1. Training notebooks (Phase 3 model comparison, Phase 4 SHAP, Phase 5 model saving)
  2. The backend inference service (later, when predicting on a live daily questionnaire submission)

Keeping the logic in one shared file guarantees training-time and prediction-time
preprocessing never drift apart.
"""

import pandas as pd
from datetime import date
from sklearn.model_selection import train_test_split, StratifiedKFold


# ---------------------------------------------------------------------------
# 1. LOAD DATA
# ---------------------------------------------------------------------------

def load_data(path: str) -> pd.DataFrame:
    """Load the raw StressLevelDataset.csv."""
    df = pd.read_csv(path)
    return df


# ---------------------------------------------------------------------------
# 2. DATA QUALITY VALIDATION (documents Phase 1 findings, re-checked here so
#    the pipeline fails loudly if a future data refresh introduces real issues)
# ---------------------------------------------------------------------------

def validate_data_quality(df: pd.DataFrame) -> dict:
    """
    Re-verify the data-quality findings from Phase 1 EDA:
      - 0 missing values
      - 0 duplicate rows
      - all features within their expected bounded ranges

    Returns a summary dict. Raises an AssertionError if something has changed
    since Phase 1 (e.g., a future dataset refresh introduces real missing data) —
    this is intentional: preprocessing should fail loudly rather than silently
    proceed on data that no longer matches what was validated.
    """
    summary = {
        "n_rows": len(df),
        "n_missing": int(df.isnull().sum().sum()),
        "n_duplicates": int(df.duplicated().sum()),
    }

    assert summary["n_missing"] == 0, (
        f"Expected 0 missing values (per Phase 1 EDA), found {summary['n_missing']}. "
        "Add explicit imputation handling before proceeding."
    )
    assert summary["n_duplicates"] == 0, (
        f"Expected 0 duplicate rows (per Phase 1 EDA), found {summary['n_duplicates']}. "
        "Add explicit deduplication before proceeding."
    )

    # Expected valid range per feature, established during Phase 1 EDA.
    # Values outside these ranges are treated as data errors (not simply
    # "extreme but valid" — those were already confirmed in Phase 1 to sit
    # inside these bounds, e.g. noise_level/study_load extremes are within 0-5).
    expected_ranges = {
        "anxiety_level": (0, 21),
        "self_esteem": (0, 30),
        "mental_health_history": (0, 1),
        "depression": (0, 27),
        "headache": (0, 5),
        "blood_pressure": (1, 3),
        "sleep_quality": (0, 5),
        "breathing_problem": (0, 5),
        "noise_level": (0, 5),
        "living_conditions": (0, 5),
        "safety": (0, 5),
        "basic_needs": (0, 5),
        "academic_performance": (0, 5),
        "study_load": (0, 5),
        "teacher_student_relationship": (0, 5),
        "future_career_concerns": (0, 5),
        "social_support": (0, 3),
        "peer_pressure": (0, 5),
        "extracurricular_activities": (0, 5),
        "bullying": (0, 5),
        "stress_level": (0, 2),
    }

    out_of_range = {}
    for col, (lo, hi) in expected_ranges.items():
        if col in df.columns:
            bad = df[(df[col] < lo) | (df[col] > hi)]
            if len(bad) > 0:
                out_of_range[col] = len(bad)

    assert not out_of_range, f"Out-of-range values found: {out_of_range}"

    summary["out_of_range_features"] = out_of_range
    summary["status"] = "PASSED — no cleaning required (consistent with Phase 1 EDA)"
    return summary


# ---------------------------------------------------------------------------
# 3. EXAM-COUNTDOWN FEATURE (recommendation-layer only — NOT a model input)
# ---------------------------------------------------------------------------

def compute_days_remaining(exam_date: date, current_date: date = None) -> int:
    """
    Days_Remaining = Exam_Date - Current_Date

    This value is used ONLY by the recommendation engine (to prioritize
    exam-relevant advice as the exam approaches) and is explicitly EXCLUDED
    from the trained XGBoost model's input features. Reasoning:
      - It has no relationship to the training dataset (StressLevelDataset.csv
        has no date/exam field at all), so the model was never trained to
        use it meaningfully.
      - Including it as a pseudo-feature at inference time without it having
        been part of training would silently break the model's learned
        feature space and could produce unreliable predictions.

    Returns a negative integer if the exam date has already passed.
    """
    if current_date is None:
        current_date = date.today()
    return (exam_date - current_date).days


def exam_period_flag(days_remaining: int, threshold_days: int = 14) -> bool:
    """
    Simple rule-based flag used by the recommendation engine:
    True if the student is within `threshold_days` of their exam.
    Default threshold: 14 days (~2 weeks), adjustable per institution calendar.
    """
    return 0 <= days_remaining <= threshold_days


# ---------------------------------------------------------------------------
# 4. FEATURE / TARGET SPLIT
# ---------------------------------------------------------------------------

TARGET_COLUMN = "stress_level"

def split_features_target(df: pd.DataFrame):
    """Separate predictor features (X) from the target label (y)."""
    X = df.drop(columns=[TARGET_COLUMN])
    y = df[TARGET_COLUMN]
    return X, y


# ---------------------------------------------------------------------------
# 5. TRAIN / TEST SPLIT
# ---------------------------------------------------------------------------

def make_train_test_split(X, y, test_size: float = 0.2, random_state: int = 42):
    """
    80/20 stratified split. Stratification keeps the Low/Medium/High class
    balance consistent between train and test sets (important given the
    target is only mildly imbalanced: 373/358/369).
    """
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=test_size,
        random_state=random_state,
        stratify=y
    )
    return X_train, X_test, y_train, y_test


# ---------------------------------------------------------------------------
# 6. CROSS-VALIDATION SETUP (used in Phase 3 for fair model comparison)
# ---------------------------------------------------------------------------

def get_cv_splitter(n_splits: int = 5, random_state: int = 42):
    """
    Stratified 5-fold cross-validation splitter.
    Stratified (not plain KFold) for the same class-balance reason as above.
    Reused identically across all four Phase 3 models (LR, DT, RF, XGBoost)
    so their comparison is apples-to-apples.
    """
    return StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=random_state)


# ---------------------------------------------------------------------------
# 7. FEATURE SCALING — DECISION, NOT SILENTLY SKIPPED
# ---------------------------------------------------------------------------

"""
SCALING DECISION (documented explicitly for the project report):

Feature scaling (e.g., StandardScaler) is NOT applied in this pipeline.

Reasoning:
  - All 20 features are already small, bounded ordinal/integer scales
    (mostly 0-5, with anxiety_level 0-21 and self_esteem 0-30 as the
    widest ranges, self_esteem and depression follow standard PSS/PHQ-style
    scoring bounds).
  - The final selected model (XGBoost) is tree-based. Tree-based models
    split on feature thresholds and are invariant to monotonic feature
    scaling -- scaling would not change XGBoost's learned splits or
    performance.
  - Logistic Regression (compared in Phase 3) IS scale-sensitive. If LR's
    unscaled performance looks suspicious during comparison, a scaled
    variant will be added specifically for LR's benchmark run, without
    affecting the shared preprocessing pipeline used for the final model.
"""

SCALING_APPLIED = False
SCALING_RATIONALE = (
    "Not applied: all features are small bounded ordinal scales; final model "
    "(XGBoost) is tree-based and scale-invariant. Documented per-report."
)


# ---------------------------------------------------------------------------
# Convenience: run the full Phase 2 pipeline end-to-end
# ---------------------------------------------------------------------------

def run_preprocessing_pipeline(raw_csv_path: str):
    """
    Full Phase 2 pipeline: load -> validate -> split features/target
    -> train/test split -> return everything needed for Phase 3.
    """
    df = load_data(raw_csv_path)
    quality_report = validate_data_quality(df)
    X, y = split_features_target(df)
    X_train, X_test, y_train, y_test = make_train_test_split(X, y)
    cv = get_cv_splitter()

    return {
        "df": df,
        "quality_report": quality_report,
        "X": X, "y": y,
        "X_train": X_train, "X_test": X_test,
        "y_train": y_train, "y_test": y_test,
        "cv_splitter": cv,
    }


if __name__ == "__main__":
    # Quick self-test when run directly: python src/data_preprocessing.py
    results = run_preprocessing_pipeline("data/raw/StressLevelDataset.csv")
    print("Data quality report:", results["quality_report"])
    print("Train shape:", results["X_train"].shape)
    print("Test shape:", results["X_test"].shape)
    print("Scaling applied:", SCALING_APPLIED, "-", SCALING_RATIONALE)

    # Exam-countdown demo
    from datetime import date
    demo_exam_date = date(2026, 9, 15)
    demo_today = date(2026, 8, 30)
    days_left = compute_days_remaining(demo_exam_date, demo_today)
    print(f"Demo: {days_left} days remaining -> exam_period_flag = {exam_period_flag(days_left)}")
