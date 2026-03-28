"""API Permis de construire"""
from fastapi import APIRouter
from app.agents.permis_construire_agent import run_permis_scraper
import threading

router = APIRouter()


@router.post("/permis/scrape")
def scrape_permis():
    """Lance le scraping des permis de construire en arrière-plan."""
    t = threading.Thread(target=run_permis_scraper, daemon=True)
    t.start()
    return {"status": "started", "message": "Scraping permis de construire lancé"}


@router.post("/permis/scrape-sync")
def scrape_permis_sync():
    """Lance le scraping en mode synchrone (pour tests)."""
    return run_permis_scraper()