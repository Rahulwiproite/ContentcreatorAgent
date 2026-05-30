import logging
from apscheduler.schedulers.background import BackgroundScheduler

from ..db import SessionLocal
from ..routers.trends import refresh_twitter_trends

log = logging.getLogger("scheduler")
scheduler = BackgroundScheduler()


def _job_refresh_trends():
    db = SessionLocal()
    try:
        refresh_twitter_trends(db)
        log.info("Refreshed Twitter trends cache")
    except Exception as e:
        log.warning("Trend refresh failed: %s", e)
    finally:
        db.close()


def start():
    if scheduler.running:
        return
    scheduler.add_job(_job_refresh_trends, "interval", hours=6, id="trends_refresh", replace_existing=True)
    scheduler.start()
