import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .db import init_db
from .default_user import ensure_default_user
from .routers import auth, social, analytics, trends, ideas, agent
from .services.scheduler import start as start_scheduler

logging.basicConfig(level=logging.INFO)
settings = get_settings()

app = FastAPI(title="ContentcreatorAgent API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agent.router)
app.include_router(auth.router)
app.include_router(social.router)
app.include_router(analytics.router)
app.include_router(trends.router)
app.include_router(ideas.router)


@app.on_event("startup")
def on_startup():
    init_db()
    ensure_default_user()
    try:
        start_scheduler()
    except Exception as e:
        logging.warning("Scheduler failed to start: %s", e)


@app.get("/healthz")
def healthz():
    return {"ok": True}


# Serve the built React SPA from /app/static if present. The unified Docker
# image copies `frontend/dist` here. When running backend-only (local dev),
# this directory may not exist; in that case the API root just responds JSON.
_STATIC_DIR = Path(__file__).parent / "static"
if _STATIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(_STATIC_DIR), html=True), name="spa")
else:
    @app.get("/")
    def root():
        return {"name": "contentcreator-agent", "status": "ok"}
