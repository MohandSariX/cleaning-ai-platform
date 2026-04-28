"""API DVF — Transactions immobilières"""
from fastapi import APIRouter
from app.agents.dvf_agent import run_dvf_scraper
import threading

router = APIRouter()


@router.post("/dvf/scrape")
def scrape_dvf():
    """Lance le scraping des transactions DVF en arrière-plan."""
    t = threading.Thread(target=run_dvf_scraper, daemon=True)
    t.start()
    return {"status": "started", "message": "Scraping DVF lancé"}


@router.post("/dvf/scrape-sync")
def scrape_dvf_sync():
    """Lance le scraping en mode synchrone (pour tests)."""
    return run_dvf_scraper()
