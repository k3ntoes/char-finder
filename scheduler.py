"""Background periodic job scheduler and ntfy alerting module using APScheduler."""

import logging
from typing import Any, Dict, Optional

import httpx
from apscheduler.schedulers.background import BackgroundScheduler

from db import DB_PATH
from fetcher import fetch_and_process_market, get_setting, send_ntfy_notification

logger = logging.getLogger(__name__)

_scheduler: Optional[BackgroundScheduler] = None


def send_ntfy_alert(
    topic: str,
    title: str,
    message: str,
    tags: str | list = "fire,money_bag",
    priority: str | int = "high",
    click_url: str = "https://thesyndicate.games/market",
) -> bool:
    """Send push notification via ntfy.sh with custom tags, priority, and error handling using JSON payload.
    
    Safe from network failures.
    """
    if not topic or not topic.strip():
        return False
    url = f"https://ntfy.sh/{topic.strip()}"
    try:
        # Parse tags
        if isinstance(tags, str):
            tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        elif isinstance(tags, list):
            tag_list = [str(t).strip() for t in tags if str(t).strip()]
        else:
            tag_list = ["fire", "money_bag"]

        # Parse priority mapping if string
        priority_mapping = {
            "min": 1,
            "low": 2,
            "default": 3,
            "high": 4,
            "max": 5,
            "urgent": 5,
        }
        if isinstance(priority, str):
            p_lower = priority.lower()
            p_val = priority_mapping.get(p_lower, 4)
        elif isinstance(priority, int):
            p_val = max(1, min(5, priority))
        else:
            p_val = 4

        payload = {
            "title": title,
            "message": message,
            "tags": tag_list,
            "click": click_url,
            "priority": p_val,
        }
        response = httpx.post(url, json=payload, timeout=5.0)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Failed to send ntfy alert to topic '{topic}': {e}")
        return False


def get_scheduler() -> BackgroundScheduler:
    """Get or create the background APScheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler()
    return _scheduler


def run_scheduled_poll() -> Dict[str, Any]:
    """Periodic job routine: fetch market data, compute HBDS scores, save history, and trigger alerts."""
    logger.info("Running scheduled market poll & HBDS evaluation job...")
    try:
        result = fetch_and_process_market()
        logger.info(
            f"Scheduled poll completed successfully: status={result.get('status')}, "
            f"steals_detected={result.get('steals_detected', 0)}, "
            f"notifications_sent={result.get('notifications_sent', 0)}"
        )
        return result
    except Exception as e:
        logger.error(f"Error during scheduled market poll: {e}")
        return {"status": "error", "message": str(e)}


def start_scheduler(interval_minutes: int = 5) -> BackgroundScheduler:
    """Start the background scheduler and register the periodic market poll job."""
    sched = get_scheduler()
    if not sched.running:
        sched.start()
        logger.info("APScheduler started successfully.")

    job_id = "market_poll_job"
    if not sched.get_job(job_id):
        sched.add_job(
            run_scheduled_poll,
            'interval',
            minutes=interval_minutes,
            id=job_id,
            replace_existing=True,
        )
        logger.info(f"Registered market poll job with interval {interval_minutes} minutes.")
    return sched


def stop_scheduler() -> None:
    """Gracefully stop the background scheduler if running."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("APScheduler shut down successfully.")


def get_scheduler_status() -> Dict[str, Any]:
    """Return scheduler running state and list of active scheduled jobs."""
    sched = get_scheduler()
    jobs = []
    if sched.running:
        for job in sched.get_jobs():
            jobs.append(
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run_time": str(job.next_run_time) if job.next_run_time else None,
                }
            )
    return {
        "running": sched.running,
        "jobs": jobs,
    }
