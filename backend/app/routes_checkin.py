import json
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import config, ml_service
from .database import get_db
from .models import User, DailyResponse, Prediction
from .questionnaire import QUESTIONS, QUESTION_KEYS
from .recommendation import build_recommendations, early_warning, classify_trend
from .schemas import CheckinRequest
from .security import get_current_user
from .services import exam_info, predictions_between, recent_history, prediction_payload

router = APIRouter(tags=["check-ins"])


@router.get("/questions")
def questions():
    """Questionnaire definition; the frontend renders the daily check-in from this."""
    return {"questions": QUESTIONS}


@router.get("/insights/global")
def global_insights():
    """Overall feature importance (mean |SHAP|) from the trained model."""
    return {"features": ml_service.global_importance()}


@router.post("/checkins", status_code=201)
def submit_checkin(body: CheckinRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    today = date.today()
    day = body.date or today
    if day != today and not config.ALLOW_BACKDATED_CHECKINS:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Check-ins can only be submitted for today")
    if day > today:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Check-in date cannot be in the future")
    if db.scalar(select(DailyResponse).where(DailyResponse.user_id == user.user_id, DailyResponse.response_date == day)):
        raise HTTPException(status.HTTP_409_CONFLICT, "You've already checked in for this day")

    result = ml_service.predict_with_explanation(body.answers, user.mental_health_history)

    response = DailyResponse(user_id=user.user_id, response_date=day, **body.answers)
    db.add(response)
    db.flush()
    db.add(Prediction(
        response_id=response.response_id, user_id=user.user_id,
        predicted_stress_level=result["predicted_class"], prediction_confidence=result["confidence"],
        risk_score=result["risk_score"],
        shap_top_factors=json.dumps({"probabilities": result["probabilities"],
                                     "explanation": result["explanation"],
                                     "stress_drivers": result["stress_drivers"]}),
    ))
    db.commit()

    return build_checkin_result(db, user, day)


def build_checkin_result(db: Session, user: User, day: date) -> dict:
    """Full result for one stored check-in: prediction, comparison, exam, early warning, recommendations.
    Shared by POST /checkins and GET /checkins/today so a page refresh shows the same result."""
    row = db.execute(
        select(DailyResponse, Prediction).join(Prediction, Prediction.response_id == DailyResponse.response_id)
        .where(DailyResponse.user_id == user.user_id, DailyResponse.response_date == day)
    ).first()
    response, pred = row
    result = prediction_payload(pred)

    exam = exam_info(user, day)
    history = recent_history(db, user.user_id, day, limit=7)
    earlier = [(d, p) for d, p in history if d < day]
    previous_risk = earlier[-1][1].risk_score if earlier else None

    # Weekly trend (this 7-day window vs the one before) feeds the recommendation engine
    cur = [p.risk_score for _, p in predictions_between(db, user.user_id, day - timedelta(days=6), day)]
    prev = [p.risk_score for _, p in predictions_between(db, user.user_id, day - timedelta(days=13), day - timedelta(days=7))]
    weekly_trend = classify_trend(sum(cur) / len(cur) if cur else None, sum(prev) / len(prev) if prev else None)

    warning = early_warning([p.risk_score for _, p in history][-3:], [p.predicted_stress_level for _, p in history][-3:])
    recs = build_recommendations(result, exam["days_remaining"], previous_risk, weekly_trend)

    return {
        "completed": True,
        "date": day.isoformat(),
        "answers": {k: getattr(response, k) for k in QUESTION_KEYS},
        "prediction": result,
        "comparison": {"previous_risk_score": previous_risk,
                       "change": round(result["risk_score"] - previous_risk, 2) if previous_risk is not None else None},
        "exam": exam,
        "early_warning": warning,
        "recommendations": recs,
    }


@router.get("/checkins/today")
def today_checkin(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    today = date.today()
    if not predictions_between(db, user.user_id, today, today):
        return {"completed": False, "date": today.isoformat(), "exam": exam_info(user, today)}
    return build_checkin_result(db, user, today)


@router.get("/checkins/history")
def history(days: int = Query(14, ge=1, le=90), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    today = date.today()
    rows = predictions_between(db, user.user_id, today - timedelta(days=days - 1), today)
    return {"days": days, "entries": [
        {"date": d.isoformat(), "risk_score": p.risk_score,
         "label": ["Low", "Medium", "High"][p.predicted_stress_level]} for d, p in rows]}
