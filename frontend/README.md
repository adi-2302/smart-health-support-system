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

## Automated browser tests (end-to-end)
30 tests drive the real app in a real browser against the real backend: registration and login errors, the full
check-in, results, early warning, weekly report, settings, theme, privacy between users, a tampered token, the backend
being down, phone width and keyboard use. Their titles use the same TC numbers as `MindTrack_Manual_Test_Cases.xlsx`.

They start their **own** backend (port 8001, throwaway database) and frontend (port 5174), so your real data is never
touched and your dev servers can stay open. Run from `frontend/`:
```bash
npm install                   # once (already done if you ran the app)
npx playwright install chromium   # once: downloads the test browser (~150 MB)
npm run test:e2e              # about 2 minutes
npx playwright show-report e2e-report    # optional: browse the HTML report with screenshots
```
- Needs `python` on your PATH (set `PYTHON=py` or a full path if yours has another name) and the backend packages installed.
- If the browser download is blocked, use the Chrome you already have: PowerShell `$env:PW_CHANNEL="chrome"; npm run test:e2e`
  (Command Prompt: `set PW_CHANNEL=chrome` then `npm run test:e2e`).
- Screenshots are saved in `e2e-results/` (two named screenshots: `result-high.png`, `mobile-dashboard.png`).

## Unit tests and build
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
