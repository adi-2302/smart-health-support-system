"""Central configuration. Override via environment variables in production."""
import os
from pathlib import Path

# Repo root = two levels above this file (backend/app/config.py -> repo root)
REPO_ROOT = Path(__file__).resolve().parents[2]

MODEL_PATH = Path(os.getenv("MODEL_PATH", REPO_ROOT / "models" / "xgboost_model_v2.pkl"))
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{REPO_ROOT / 'backend' / 'mindtrack.db'}")

# IMPORTANT: set a real secret in production (export SECRET_KEY=...). This default is for development only.
SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")
TOKEN_EXPIRE_HOURS = int(os.getenv("TOKEN_EXPIRE_HOURS", "24"))

# Development convenience: lets the demo/tests submit a check-in for a past date so
# multi-day trends and the early-warning alert can be shown without waiting days.
# Set ALLOW_BACKDATED_CHECKINS=false in production.
ALLOW_BACKDATED_CHECKINS = os.getenv("ALLOW_BACKDATED_CHECKINS", "true").lower() == "true"

# Exam-period threshold (days) used by the recommendation engine
EXAM_PERIOD_DAYS = 14
