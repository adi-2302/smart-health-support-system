"""Rule-based recommendation engine.

Inputs combined (as specified in the PRD):
  1. the model's prediction (class + 0-10 risk score)
  2. SHAP stress drivers (which factors pushed this prediction toward High)
  3. days remaining until the student's exam
  4. the previous check-in's risk score
  5. the weekly trend
The ML model does the predicting; these rules only decide what to *suggest*. They are
general wellbeing suggestions, not medical advice or diagnosis.
"""
from . import config

RISING_ALERT_FLOOR = 4.0  # 0-10 risk score; below this a rising trend is not alerted

# What to suggest when a given factor is a top driver of today's stress
DRIVER_ADVICE = {
    "anxiety_level": ("Try a 5-minute grounding break", "Slow breathing (in for 4, out for 6) or a short walk before your next task can ease anxious load."),
    "self_esteem": ("Note three things that went well", "Writing down small wins today helps counter harsh self-judgement."),
    "depression": ("Reach out to someone you trust", "A short conversation, even a message, can shift how the rest of the day feels."),
    "headache": ("Rest your eyes and hydrate", "Step away from screens for 10 minutes and drink some water; persistent headaches are worth mentioning to a doctor."),
    "blood_pressure": ("Take a short walk and slow your breathing", "Brief movement and calm breathing between study sessions can help; if readings stay high, check in with a doctor."),
    "sleep_quality": ("Protect tonight's sleep", "Set a fixed wind-down time and keep screens away for the last 30 minutes before bed."),
    "breathing_problem": ("Pause and breathe slowly", "If breathlessness is frequent or severe, please see a doctor rather than relying on this app."),
    "noise_level": ("Find a quieter study spot", "Try the library, headphones with low-volume ambient sound, or a quieter time of day."),
    "living_conditions": ("Make one small change to your space", "Tidying your desk or improving lighting can noticeably help focus and mood."),
    "safety": ("Talk to your hostel warden or department contact", "Feeling unsafe has an outsized effect on stress; you shouldn't have to handle it alone."),
    "basic_needs": ("Cover the basics first", "Regular meals, water and rest come before extra studying; ask your college for support if essentials are a struggle."),
    "academic_performance": ("Pick one subject and make a small, concrete plan", "Revisiting one recent assignment or topic with a clear goal can rebuild confidence."),
    "study_load": ("Break the workload into smaller blocks", "List tasks, pick the top three for today, and schedule short breaks between them."),
    "teacher_student_relationship": ("Ask one specific question in office hours", "A short, focused conversation with a faculty member often clears more than hours alone."),
    "future_career_concerns": ("Turn one career worry into a next step", "Pick a single action (update your CV, talk to a senior, check one opening) instead of carrying the whole worry."),
    "social_support": ("Spend time with someone supportive", "Even 20 minutes with a friend or family member helps; consider joining a study group."),
    "peer_pressure": ("It's okay to say no", "Choosing your own pace for studies and activities protects your energy."),
    "extracurricular_activities": ("Consider pausing one commitment this week", "Your activity load is a leading factor today; a temporary pause can free up recovery time."),
    "bullying": ("Please tell someone you trust, or your college's anti-bullying cell", "You don't have to deal with this alone, and reporting it is a reasonable step."),
}


def _exam_recs(pred_class: int, days: int | None) -> list[dict]:
    if days is None or days < 0 or days > config.EXAM_PERIOD_DAYS:
        return []
    when = "today" if days == 0 else f"in {days} day{'s' if days != 1 else ''}"
    recs = []
    if days <= 3:
        recs.append({"title": f"Exam {when}: protect sleep over last-minute cramming",
                     "detail": "Light revision of key points, a proper meal, and a full night's sleep will help more than late-night cramming.",
                     "reason": "exam", "priority": 1})
    elif pred_class == 2:
        recs.append({"title": f"Exam {when}: shorter revision blocks with real breaks",
                     "detail": "Try 40 minutes of focused study followed by a 10-minute break, and drop the topics you can't realistically cover.",
                     "reason": "exam", "priority": 1})
    elif pred_class == 1:
        recs.append({"title": f"Exam {when}: plan your remaining revision",
                     "detail": "Split the remaining syllabus across the days left so no single day feels overloaded.",
                     "reason": "exam", "priority": 2})
    else:
        recs.append({"title": f"Exam {when}: good moment to consolidate",
                     "detail": "You're in a steady place, so use it for active recall (practice questions) rather than re-reading.",
                     "reason": "exam", "priority": 3})
    return recs


def build_recommendations(prediction: dict, days_remaining: int | None, previous_risk: float | None,
                          weekly_trend: str | None = None) -> list[dict]:
    recs: list[dict] = []
    cls, risk = prediction["predicted_class"], prediction["risk_score"]

    # 1. Support nudge for very high readings
    if cls == 2 and risk >= 7:
        recs.append({"title": "Consider talking to your college counsellor or someone you trust",
                     "detail": "Today's reading is high. Speaking to someone can help, and you don't need to wait for things to get worse.",
                     "reason": "high_risk", "priority": 1})

    # 2. Advice for the top SHAP stress drivers
    for rank, d in enumerate(prediction["stress_drivers"][:2]):
        advice = DRIVER_ADVICE.get(d["feature"])
        if advice:
            recs.append({"title": advice[0], "detail": advice[1],
                         "reason": f"driver:{d['feature']}", "priority": 1 if rank == 0 else 2})

    # 3. Exam-aware advice
    recs.extend(_exam_recs(cls, days_remaining))

    # 4. Day-over-day change
    if previous_risk is not None:
        delta = risk - previous_risk
        if delta >= 1.0:
            recs.append({"title": "Stress is higher than at your last check-in",
                         "detail": "If you can, make tomorrow a little lighter and keep your sleep and meal times regular.",
                         "reason": "trend_up", "priority": 2})
        elif delta <= -1.0:
            recs.append({"title": "Stress is lower than at your last check-in",
                         "detail": "Whatever you did recently seems to be helping; try to repeat it.",
                         "reason": "trend_down", "priority": 3})

    # 5. Weekly trend
    if weekly_trend == "rising":
        recs.append({"title": "Your week has been trending upward",
                     "detail": "Consider scheduling a proper rest block in the next two days before it builds further.",
                     "reason": "weekly_trend", "priority": 2})

    # 6. Nothing notable
    if not recs:
        recs.append({"title": "Keep doing what you're doing",
                     "detail": "Nothing stands out as a strong stress driver today. A good day to maintain your routine.",
                     "reason": "steady", "priority": 3})

    recs.sort(key=lambda r: r["priority"])
    return recs


def early_warning(risk_history: list[float], label_history: list[int] | None = None) -> dict:
    """risk_history: oldest -> newest risk scores (include today's).
    Rule A (rising): last 3 check-ins strictly increase, total rise >= 1.0 point, AND the latest
            reading is at least RISING_ALERT_FLOOR (so a rise from 0.2 to 3 doesn't alert while the
            student is still comfortably low; avoids alert fatigue from ordinary day-to-day noise).
    Rule B (sustained high): last 2 check-ins both predicted High (class 2).
    Thresholds are design choices, not validated on real longitudinal data; tune with pilot data."""
    if len(risk_history) >= 3:
        a, b, c = risk_history[-3:]
        if a < b < c and (c - a) >= 1.0 and c >= RISING_ALERT_FLOOR:
            return {"triggered": True, "type": "rising",
                    "message": "Stress has risen across your last 3 check-ins.",
                    "risk_trend": [round(x, 2) for x in risk_history[-3:]]}
    if label_history and len(label_history) >= 2 and label_history[-1] == 2 and label_history[-2] == 2:
        return {"triggered": True, "type": "sustained_high",
                "message": "Your stress has been in the High range for 2 check-ins in a row.",
                "risk_trend": [round(x, 2) for x in risk_history[-2:]]}
    return {"triggered": False, "type": None, "message": None, "risk_trend": [round(x, 2) for x in risk_history[-3:]]}


def classify_trend(current_avg: float | None, previous_avg: float | None, threshold: float = 0.5) -> str | None:
    if current_avg is None or previous_avg is None:
        return None
    d = current_avg - previous_avg
    return "rising" if d >= threshold else "falling" if d <= -threshold else "stable"
