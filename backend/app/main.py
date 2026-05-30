import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .db import init_db
from .default_user import ensure_default_user
from .routers import auth, social, analytics, trends, ideas, agent
from .services.scheduler import start as start_scheduler

logging.basicConfig(level=logging.INFO)
settings = get_settings()

app = FastAPI(title="Comedy Content Agent API", version="2.0.0")

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


@app.get("/")
def root():
    return {"name": "comedy-content-agent", "status": "ok"}


@app.get("/healthz")
def healthz():
    return {"ok": True}
