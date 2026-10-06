"""Shared helpers used by the routers."""
import json
from datetime import date, timedelta
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import config
from .models import User, ExamSchedule, DailyResponse, Prediction


def active_exam(user: User) -> ExamSchedule | None:
    return user.exams[0] if user.exams else None  # relationship ordered by updated_at desc


def exam_info(user: User, today: date) -> dict:
    exam = active_exam(user)
    if exam is None:
        return {"exam_date": None, "exam_label": None, "days_remaining": None, "in_exam_period": False}
    days = (exam.exam_date - today).days
    return {"exam_date": exam.exam_date.isoformat(), "exam_label": exam.exam_label,
            "days_remaining": days, "in_exam_period": 0 <= days <= config.EXAM_PERIOD_DAYS}


def predictions_between(db: Session, user_id: int, start: date, end: date):
    """Predictions (with their response date) for start <= date <= end, oldest first."""
    rows = db.execute(
        select(DailyResponse.response_date, Prediction)
        .join(Prediction, Prediction.response_id == DailyResponse.response_id)
        .where(DailyResponse.user_id == user_id, DailyResponse.response_date >= start,
               DailyResponse.response_date <= end)
        .order_by(DailyResponse.response_date)
    ).all()
    return rows


def recent_history(db: Session, user_id: int, up_to: date, limit: int = 3):
    """Last `limit` predictions on or before `up_to`, oldest -> newest."""
    rows = db.execute(
        select(DailyResponse.response_date, Prediction)
        .join(Prediction, Prediction.response_id == DailyResponse.response_id)
        .where(DailyResponse.user_id == user_id, DailyResponse.response_date <= up_to)
        .order_by(DailyResponse.response_date.desc()).limit(limit)
    ).all()
    return list(reversed(rows))


def prediction_payload(pred: Prediction) -> dict:
    stored = json.loads(pred.shap_top_factors) if pred.shap_top_factors else {}
    return {
        "predicted_class": pred.predicted_stress_level,
        "predicted_label": ["Low", "Medium", "High"][pred.predicted_stress_level],
        "confidence": pred.prediction_confidence,
        "risk_score": pred.risk_score,
        "probabilities": stored.get("probabilities", {}),
        "explanation": stored.get("explanation", []),
        "stress_drivers": stored.get("stress_drivers", []),
    }
