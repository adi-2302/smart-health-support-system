# MindTrack frontend (React + Vite)

Web UI for the Smart Mental Health Support System. It talks to the FastAPI backend in `../backend`.

## Pages
Login · Register · Dashboard (today + 14-day trend + exam countdown) · Daily check-in (19 multiple-choice
questions, rendered from `GET /questions`) · Result (risk score, SHAP "why", recommendations, early warning) ·
Weekly report · Insights (global SHAP importance) · Profile · Settings (exam date, light/dark theme).

## Run it (two terminals)
Needs **Node.js LTS** (https://nodejs.org) and the backend dependencies installed.

Terminal 1 - backend (from the repo root):
```bash
cd backend
python -m uvicorn app.main:app --reload       # http://localhost:8000
python seed_demo.py                           # optional: demo login with a week of data (run once, before or after)
```
Terminal 2 - frontend:
```bash
cd frontend
npm install
npm run dev                                   # http://localhost:5173
```
Open http://localhost:5173. Demo login after `seed_demo.py`: `demo@mindtrack.test` / `demo-pass-123`.

If the backend runs somewhere else, copy `.env.example` to `.env` and set `VITE_API_URL`.

## Tests and build
```bash
npm test          # unit tests for date handling, risk bands, API error messages
npm run build     # production bundle in dist/
```

## Notes
- The login token is kept in `localStorage` (fine for a college project; a production app would use httpOnly cookies).
- Dates use the browser's local calendar day (not UTC) so a morning check-in in India isn't dated yesterday.
- Risk bands used for colours: 0-3.5 low, 3.5-6.5 medium, 6.5-10 high. The badge shows the model's most likely
  class, which can differ from the band of the score because the score is probability-weighted.
- Scores are a self-reflection aid, not a diagnosis (the app says so on the result page).
