"""carWeights FastAPI app: JSON API under /api + static frontend at /."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .routes import router as api_router

app = FastAPI(title="carWeights — Hungarian Car Weights & Budapest Parking Fee")
app.include_router(api_router, prefix="/api")

_WEB = Path(__file__).resolve().parent.parent / "web"
app.mount("/", StaticFiles(directory=str(_WEB), html=True), name="web")
