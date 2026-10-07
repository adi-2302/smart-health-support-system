# MindTrack backend (FastAPI)

REST API for the Smart Mental Health Support System. Wraps the trained XGBoost model
(`models/xgboost_model_v2.pkl`) + SHAP explanations, stores check-ins in SQLite, and
generates recommendations, weekly reports and early-warning alerts.

## Run it (from the repo root, inside your virtual environment)
```bash
pip install -r backend/requirements.txt
cd backend
uvicorn app.main:app --reload          # API on http://localhost:8000
```
Interactive docs (try every endpoint in the browser): http://localhost:8000/docs

## Run the tests
```bash
cd backend
pytest -q                               # 15 tests, uses a throwaway database
```

## Endpoints
| Method | Path | Purpose |
|---|---|---|
| POST | `/auth/register` | Create account; exam date is collected once here |
| POST | `/auth/login` | Returns a JWT (send as `Authorization: Bearer <token>`) |
| GET | `/profile` | Profile + exam countdown |
| PUT | `/profile/exam` | Update exam date |
| GET | `/exam/countdown` | `days_remaining = exam_date - today` (auto-calculated) |
| GET | `/questions` | The 19 check-in questions + options (frontend renders from this) |
| POST | `/checkins` | Submit daily answers -> prediction, SHAP explanation, recommendations, early warning |
| GET | `/checkins/today` | Today's full result (prediction, SHAP, answers, recommendations, early warning) or `completed: false` |
| GET | `/checkins/history?days=14` | Risk-score history |
| GET | `/reports/weekly` | Weekly report: trend, best/worst day, vs last week, SHAP factors, recommendations |
| GET | `/insights/global` | Overall feature importance (mean abs SHAP) |
| GET | `/health` | Liveness check |

## Configuration (environment variables)
`SECRET_KEY` (**set this in production**), `DATABASE_URL`, `MODEL_PATH`, `TOKEN_EXPIRE_HOURS`,
`ALLOW_BACKDATED_CHECKINS` (default `true` for demos/tests so multi-day trends can be shown;
set `false` in production).

## Design notes and known limitations (worth stating in the report)
- **Questionnaire -> model scale mapping.** The model was trained on StressLevelDataset.csv, whose
  features use different native scales (anxiety 0-21, self-esteem 0-30, ...). The 5-option answers are
  linearly rescaled onto those ranges (`ml_service.py`). This is an approximation: the model has not been
  validated on answers collected through this questionnaire.
- **Model v2.** Week 5's grid search optimised F1 and chose learning_rate 0.01, giving correct classes but
  near-uniform probabilities. `src/train_final_model.py` re-selects hyperparameters by cross-validated
  log-loss on the training split only. Test accuracy is unchanged (87.7% vs 87.3%, within noise); log-loss
  improved 0.497 -> 0.263.
- **Risk score (0-10)** = (0.5 x P(Medium) + 1.0 x P(High)) x 10. Used for trends and alerts.
- **Early-warning thresholds** (3 rising check-ins, rise >= 1.0, latest >= 4.0; or 2 consecutive High) are
  design choices, not validated on real longitudinal data. Tune them with pilot data.
- `blood_pressure` / `breathing_problem` are self-reported, not sensor readings.
- Recommendations are general wellbeing suggestions, not medical advice.

## Demo data
`python seed_demo.py` (from `backend/`) creates `demo@mindtrack.test` / `demo-pass-123` with six earlier days of
check-ins, leaving today empty for a live demo. Delete `backend/mindtrack.db` to start from scratch.
