"""
API Scheduler — endpoints pour monitorer et contrôler le scheduler depuis le dashboard.
"""

from fastapi import APIRouter
from app.scheduler import (
    MAX_PAGES_DEFAULT, MAX_PAGES_PARIS,
    scheduler_status, run_nightly_scrape,
    get_scheduler, ZONES, QUERY_TYPES, DAY_TO_DEPT
)
from datetime import datetime
import threading

router = APIRouter()


@router.get("/scheduler/status")
def get_status():
    """Retourne l'état complet du scheduler."""
    sched = get_scheduler()
    job = sched.get_job("nightly_scrape") if sched.running else None
    return {
        **scheduler_status,
        "scheduler_running": sched.running if sched else False,
        "next_run": str(job.next_run_time) if job else None,
        "planning": {
            str(day): {"dept": dept, "cities_count": len(ZONES[dept]), "queries_count": len(QUERY_TYPES)}
            for day, dept in DAY_TO_DEPT.items()
        }
    }


@router.post("/scheduler/run-now")
def run_now():
    """Lance le scraping immédiatement (pour tester sans attendre 23h)."""
    if scheduler_status["running"]:
        return {"status": "already_running", "message": "Un scraping est déjà en cours"}
    t = threading.Thread(target=run_nightly_scrape, daemon=True)
    t.start()
    return {"status": "started", "message": "Scraping lancé manuellement"}


@router.post("/scheduler/clear-log")
def clear_log():
    scheduler_status["log"] = []
    return {"status": "ok"}


@router.get("/scheduler/planning")
def get_planning():
    """Retourne le planning complet de la semaine."""
    day_names = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
    dept_names = {
        "94": "Val-de-Marne",
        "93": "Seine-Saint-Denis",
        "92": "Hauts-de-Seine",
        "77": "Seine-et-Marne",
        "75": "Paris",
        "91": "Essonne",
        "78": "Yvelines",
    }
    return {
        "schedule": [
            {
                "day": day_names[day],
                "dept": dept,
                "dept_name": dept_names[dept],
                "cities": ZONES[dept],
                "queries": QUERY_TYPES,
                "estimated_prospects": len(ZONES[dept]) * len(QUERY_TYPES) * (MAX_PAGES_PARIS if dept == "75" else MAX_PAGES_DEFAULT) * 20,
            }
            for day, dept in DAY_TO_DEPT.items()
        ]
    }