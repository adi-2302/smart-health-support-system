from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from .database import Base, engine
from . import ml_service
from .routes_auth import router as auth_router
from .routes_checkin import router as checkin_router
from .routes_reports import router as reports_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    ml_service._load()  # load model + SHAP explainer once at startup, not per request
    yield


app = FastAPI(title="MindTrack API", version="0.1.0",
              description="Smart Mental Health Support System for Students in Higher Education", lifespan=lifespan)

# Development: allow the local React dev server. Tighten to the real frontend origin in production.
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://localhost:3000"],
                   allow_methods=["*"], allow_headers=["*"])

app.include_router(auth_router)
app.include_router(checkin_router)
app.include_router(reports_router)


@app.get("/", include_in_schema=False)
def root():
    """Send the bare address to the interactive API docs instead of a 404."""
    return RedirectResponse("/docs")


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}
