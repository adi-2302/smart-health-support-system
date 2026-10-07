"""Create a demo account with a week of check-ins so the dashboard, trend chart and weekly report
have something to show.  Run from the backend/ folder (the API does not need to be running):

    python seed_demo.py

Login afterwards:  demo@mindtrack.test / demo-pass-123
Today is deliberately left empty so you can do the live check-in during a demo.
Re-running is safe: existing demo days are skipped."""
from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.main import app
from app.questionnaire import QUESTIONS

EMAIL, PASSWORD = "demo@mindtrack.test", "demo-pass-123"
GOOD_HIGH = {"self_esteem", "sleep_quality", "living_conditions", "safety", "basic_needs",
             "academic_performance", "teacher_student_relationship", "social_support"}
# Fraction of "bad" answers per day, oldest -> yesterday: a calm week that gets harder as the exam nears.
WEEK = [0.0, 0.0, 0.15, 0.35, 0.55, 0.8]


def blend(frac_bad: float) -> dict:
    out = {}
    keys = [q["key"] for q in QUESTIONS]
    n_bad = round(frac_bad * len(keys))
    for i, q in enumerate(QUESTIONS):
        vals = [o["value"] for o in q["options"]]
        lo, hi = min(vals), max(vals)
        good, bad = (hi, lo) if q["key"] in GOOD_HIGH else (lo, hi)
        if q["key"] == "blood_pressure":
            good, bad = 2, 3
        out[q["key"]] = bad if i < n_bad else good
    return out


def main() -> None:
    with TestClient(app) as c:
        body = {"name": "Demo Student", "email": EMAIL, "password": PASSWORD, "age": 21, "course": "B.Tech AIML",
                "year": "4th", "living_conditions": "Hostel", "mental_health_history": False,
                "exam_date": (date.today() + timedelta(days=9)).isoformat(), "exam_label": "Semester 7 finals"}
        r = c.post("/auth/register", json=body)
        if r.status_code == 409:
            r = c.post("/auth/login", json={"email": EMAIL, "password": PASSWORD})
        r.raise_for_status()
        headers = {"Authorization": f"Bearer {r.json()['token']}"}
        today = date.today()
        for i, frac in enumerate(WEEK):
            day = today - timedelta(days=len(WEEK) - i)
            res = c.post("/checkins", json={"answers": blend(frac), "date": day.isoformat()}, headers=headers)
            note = f"risk {res.json()['prediction']['risk_score']}" if res.status_code == 201 else f"skipped ({res.status_code})"
            print(f"{day}  {note}")
    print(f"\nDemo login: {EMAIL} / {PASSWORD}")


if __name__ == "__main__":
    main()
