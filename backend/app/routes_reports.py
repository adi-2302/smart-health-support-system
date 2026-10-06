from collections import defaultdict
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import get_db
from .models import User, WeeklyReport
from .recommendation import build_recommendations, early_warning, classify_trend
from .security import get_current_user
from .services import exam_info, predictions_between, recent_history, prediction_payload

router = APIRouter(tags=["reports"])


@router.get("/reports/weekly")
def weekly_report(end: date | None = Query(None, description="Last day of the 7-day window (default: today)"),
                  user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    end = end or date.today()
    start = end - timedelta(days=6)
    rows = predictions_between(db, user.user_id, start, end)
    prev_rows = predictions_between(db, user.user_id, start - timedelta(days=7), start - timedelta(days=1))

    if not rows:
        return {"window": {"start": start.isoformat(), "end": end.isoformat()}, "has_data": False,
                "message": "No check-ins in this week yet."}

    daily = [{"date": d.isoformat(), "risk_score": p.risk_score,
              "label": ["Low", "Medium", "High"][p.predicted_stress_level]} for d, p in rows]
    scores = [p.risk_score for _, p in rows]
    avg = sum(scores) / len(scores)
    prev_avg = sum(p.risk_score for _, p in prev_rows) / len(prev_rows) if prev_rows else None
    trend = classify_trend(avg, prev_avg)
    highest = max(rows, key=lambda r: r[1].risk_score)
    lowest = min(rows, key=lambda r: r[1].risk_score)

    # Contributing factors: SHAP stress-driver contributions summed over the week
    totals, counts = defaultdict(float), defaultdict(int)
    for _, p in rows:
        for drv in prediction_payload(p)["stress_drivers"]:
            totals[(drv["feature"], drv["label"])] += drv["contribution"]
            counts[(drv["feature"], drv["label"])] += 1
    factors = sorted(({"feature": f, "label": l, "total_contribution": round(t, 3), "days_present": counts[(f, l)]}
                      for (f, l), t in totals.items()), key=lambda x: -x["total_contribution"])[:5]

    hist = recent_history(db, user.user_id, end, limit=3)
    warning = early_warning([p.risk_score for _, p in hist], [p.predicted_stress_level for _, p in hist])
    latest_pred = prediction_payload(rows[-1][1])
    latest_pred["risk_score"] = rows[-1][1].risk_score
    exam = exam_info(user, end)
    previous_risk = rows[-2][1].risk_score if len(rows) > 1 else None
    recs = build_recommendations(latest_pred, exam["days_remaining"], previous_risk, trend)

    # Persist a snapshot (upsert on user + week_start)
    existing = db.scalar(select(WeeklyReport).where(WeeklyReport.user_id == user.user_id,
                                                    WeeklyReport.week_start_date == start))
    rep = existing or WeeklyReport(user_id=user.user_id, week_start_date=start, week_end_date=end)
    rep.week_end_date, rep.average_stress_level = end, round(avg, 2)
    rep.highest_stress_day, rep.lowest_stress_day = highest[0], lowest[0]
    rep.previous_week_comparison, rep.early_warning_triggered = trend, int(warning["triggered"])
    rep.generated_at = datetime.utcnow()
    db.add(rep)
    db.commit()

    return {
        "has_data": True,
        "window": {"start": start.isoformat(), "end": end.isoformat()},
        "daily": daily,
        "summary": {"average_risk": round(avg, 2), "checkins": len(rows),
                    "highest_day": {"date": highest[0].isoformat(), "risk_score": highest[1].risk_score},
                    "lowest_day": {"date": lowest[0].isoformat(), "risk_score": lowest[1].risk_score}},
        "vs_previous_week": {"previous_average": round(prev_avg, 2) if prev_avg is not None else None,
                             "change": round(avg - prev_avg, 2) if prev_avg is not None else None, "trend": trend},
        "contributing_factors": factors,
        "early_warning": warning,
        "exam": exam,
        "recommendations": recs,
    }
