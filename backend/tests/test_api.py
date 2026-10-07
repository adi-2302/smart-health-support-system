"""API tests. Run from the backend/ folder:  pytest -q
Uses a throwaway SQLite database; never touches the real mindtrack.db."""
import os
import tempfile
from datetime import date, timedelta

import pytest

_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"
os.environ["ALLOW_BACKDATED_CHECKINS"] = "true"

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402
from app.questionnaire import QUESTIONS  # noqa: E402

GOOD_HIGH = {"self_esteem", "sleep_quality", "living_conditions", "safety", "basic_needs",
             "academic_performance", "teacher_student_relationship", "social_support"}


def answers(level: str) -> dict:
    """level: 'good' | 'bad'. Builds a full, valid set of answers."""
    out = {}
    for q in QUESTIONS:
        vals = [o["value"] for o in q["options"]]
        lo, hi = min(vals), max(vals)
        good = hi if q["key"] in GOOD_HIGH else lo
        bad = lo if q["key"] in GOOD_HIGH else hi
        if q["key"] == "blood_pressure":
            good, bad = 2, 3
        out[q["key"]] = good if level == "good" else bad
    return out


def blend(frac_bad: float) -> dict:
    """Mix good/bad answers to produce a gradually worsening day (0=all good, 1=all bad)."""
    g, b = answers("good"), answers("bad")
    keys = list(g)
    n_bad = round(frac_bad * len(keys))
    return {k: (b[k] if i < n_bad else g[k]) for i, k in enumerate(keys)}


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def register(client, email="student@example.com", exam_in_days=9, **extra):
    body = {"name": "Test Student", "email": email, "password": "password123", "age": 20,
            "course": "B.Tech AIML", "year": "4th", "mental_health_history": False,
            "exam_date": (date.today() + timedelta(days=exam_in_days)).isoformat(), **extra}
    return client.post("/auth/register", json=body)


def auth(token):
    return {"Authorization": f"Bearer {token}"}


# ---------- basics ----------
def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_questions_served_from_backend(client):
    qs = client.get("/questions").json()["questions"]
    assert len(qs) == 19
    assert all(len(q["options"]) in (3, 5) for q in qs)


# ---------- auth ----------
def test_register_login_and_duplicate(client):
    r = register(client, "auth1@example.com")
    assert r.status_code == 201 and r.json()["token"]
    assert register(client, "auth1@example.com").status_code == 409
    ok = client.post("/auth/login", json={"email": "AUTH1@example.com", "password": "password123"})
    assert ok.status_code == 200
    bad = client.post("/auth/login", json={"email": "auth1@example.com", "password": "wrong-password"})
    assert bad.status_code == 401


def test_register_validation(client):
    assert register(client, "not-an-email").status_code == 422
    assert client.post("/auth/register", json={"name": "x", "email": "a@b.co", "password": "short",
                                               "exam_date": "2030-01-01"}).status_code == 422


def test_protected_routes_need_token(client):
    for method, path in [("get", "/profile"), ("get", "/exam/countdown"), ("get", "/reports/weekly"),
                         ("get", "/checkins/today"), ("post", "/checkins")]:
        assert getattr(client, method)(path).status_code == 401
    assert client.get("/profile", headers=auth("garbage")).status_code == 401


# ---------- exam countdown ----------
def test_exam_countdown_and_update(client):
    token = register(client, "exam1@example.com", exam_in_days=9).json()["token"]
    c = client.get("/exam/countdown", headers=auth(token)).json()
    assert c["days_remaining"] == 9 and c["in_exam_period"] is True
    new = (date.today() + timedelta(days=40)).isoformat()
    client.put("/profile/exam", json={"exam_date": new}, headers=auth(token))
    c2 = client.get("/exam/countdown", headers=auth(token)).json()
    assert c2["days_remaining"] == 40 and c2["in_exam_period"] is False


# ---------- check-in & model ----------
def test_checkin_good_vs_bad_predictions(client):
    t1 = register(client, "good@example.com").json()["token"]
    t2 = register(client, "bad@example.com").json()["token"]
    good = client.post("/checkins", json={"answers": answers("good")}, headers=auth(t1)).json()
    bad = client.post("/checkins", json={"answers": answers("bad")}, headers=auth(t2)).json()
    assert good["prediction"]["predicted_label"] == "Low"
    assert bad["prediction"]["predicted_label"] == "High"
    assert good["prediction"]["risk_score"] < 3 < 7 < bad["prediction"]["risk_score"]


def test_checkin_response_has_explanation_and_recommendations(client):
    token = register(client, "shap@example.com", exam_in_days=2).json()["token"]
    r = client.post("/checkins", json={"answers": answers("bad")}, headers=auth(token)).json()
    exp = r["prediction"]["explanation"]
    assert len(exp) == 6 and all({"feature", "label", "contribution"} <= set(e) for e in exp)
    assert r["prediction"]["stress_drivers"], "high-stress day should have SHAP drivers"
    assert abs(sum(r["prediction"]["probabilities"].values()) - 1) < 0.01
    reasons = {x["reason"] for x in r["recommendations"]}
    assert "exam" in reasons, "exam 2 days away should produce an exam-aware recommendation"
    assert any(x.startswith("driver:") for x in reasons)
    assert r["exam"]["days_remaining"] == 2


def test_one_checkin_per_day_and_validation(client):
    token = register(client, "dup@example.com").json()["token"]
    assert client.post("/checkins", json={"answers": answers("good")}, headers=auth(token)).status_code == 201
    assert client.post("/checkins", json={"answers": answers("good")}, headers=auth(token)).status_code == 409
    incomplete = answers("good"); incomplete.pop("sleep_quality")
    assert client.post("/checkins", json={"answers": incomplete,
                                          "date": (date.today() - timedelta(days=1)).isoformat()}, headers=auth(token)).status_code == 422
    invalid = answers("good"); invalid["anxiety_level"] = 9
    assert client.post("/checkins", json={"answers": invalid,
                                          "date": (date.today() - timedelta(days=1)).isoformat()}, headers=auth(token)).status_code == 422
    future = (date.today() + timedelta(days=1)).isoformat()
    assert client.post("/checkins", json={"answers": answers("good"), "date": future}, headers=auth(token)).status_code == 422


def test_today_endpoint(client):
    token = register(client, "today@example.com").json()["token"]
    assert client.get("/checkins/today", headers=auth(token)).json()["completed"] is False
    posted = client.post("/checkins", json={"answers": answers("good")}, headers=auth(token)).json()
    today = client.get("/checkins/today", headers=auth(token)).json()
    assert today["completed"] is True
    # a refresh must return the same full result, not just the prediction
    assert today["prediction"]["risk_score"] == posted["prediction"]["risk_score"]
    assert today["answers"] == answers("good")
    assert {"comparison", "exam", "early_warning", "recommendations"} <= set(today)
    assert today["recommendations"] == posted["recommendations"]


def test_cors_allows_local_dev_origins(client):
    for origin in ("http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:4173"):
        r = client.get("/health", headers={"Origin": origin})
        assert r.headers.get("access-control-allow-origin") == origin
    r = client.get("/health", headers={"Origin": "http://evil.example.com"})
    assert "access-control-allow-origin" not in r.headers


# ---------- trend, early warning, weekly report ----------
def test_rising_trend_triggers_early_warning_and_weekly_report(client):
    token = register(client, "trend@example.com", exam_in_days=5).json()["token"]
    h = auth(token)
    fracs = [0.0, 0.0, 0.15, 0.35, 0.55, 0.8, 1.0]  # gradually worsening week
    results = []
    for i, f in enumerate(fracs):
        d = (date.today() - timedelta(days=len(fracs) - 1 - i)).isoformat()
        r = client.post("/checkins", json={"answers": blend(f), "date": d}, headers=h)
        assert r.status_code == 201, r.text
        results.append(r.json())

    risks = [r["prediction"]["risk_score"] for r in results]
    assert risks[-1] > risks[0], f"risk should rise across the week: {risks}"
    # Early warning must trigger at some point in a worsening run, and not on the first (healthy) days
    assert results[0]["early_warning"]["triggered"] is False
    # Rising but still low (risk < 4) must NOT alert; once the rise reaches Medium territory it must
    low_rising = [r for r in results if r["prediction"]["risk_score"] < 4]
    assert all(r["early_warning"]["triggered"] is False for r in low_rising)
    assert results[-1]["early_warning"]["triggered"] is True and results[-1]["early_warning"]["type"] == "rising"
    assert results[-1]["comparison"]["previous_risk_score"] is not None

    rep = client.get("/reports/weekly", headers=h).json()
    assert rep["has_data"] and rep["summary"]["checkins"] == 7 and len(rep["daily"]) == 7
    assert rep["summary"]["highest_day"]["risk_score"] >= rep["summary"]["lowest_day"]["risk_score"]
    assert rep["contributing_factors"] and rep["recommendations"]
    assert rep["early_warning"]["triggered"] is True
    assert rep["exam"]["days_remaining"] == 5


def test_weekly_report_empty_and_comparison(client):
    token = register(client, "empty@example.com").json()["token"]
    assert client.get("/reports/weekly", headers=auth(token)).json()["has_data"] is False


def test_backdating_can_be_disabled(client, monkeypatch):
    from app import config
    monkeypatch.setattr(config, "ALLOW_BACKDATED_CHECKINS", False)
    token = register(client, "nobackdate@example.com").json()["token"]
    y = (date.today() - timedelta(days=1)).isoformat()
    assert client.post("/checkins", json={"answers": answers("good"), "date": y}, headers=auth(token)).status_code == 403


def test_global_insights(client):
    feats = client.get("/insights/global").json()["features"]
    assert len(feats) == 20
    assert feats[0]["feature"] == "blood_pressure"          # matches the SHAP finding in Week 6
    assert feats == sorted(feats, key=lambda f: -f["importance"])
