from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
import threading

from app.agents.lead_scraper import run_lead_scraper
from app.agents.lead_scorer import run_lead_scoring

router = APIRouter()

# État global du scraping (en mémoire)
scrape_status = {"running": False, "log": [], "done": 0, "total": 0}


class ScrapeParams(BaseModel):
    query: str = "nettoyage"
    locations: List[str] = ["Paris"]
    max_pages: int = 2
    run_scoring: bool = True


def _run_scrape(params: ScrapeParams):
    try:
        scrape_status["log"].append(f"🚀 Démarrage — {len(params.locations)} ville(s), {params.max_pages} page(s)/ville")
        scrape_status["log"].append(f"🔍 Recherche : « {params.query} »")
        run_lead_scraper(query=params.query, locations=params.locations, max_pages=params.max_pages)
        scrape_status["log"].append("✅ Scraping terminé")
        if params.run_scoring:
            scrape_status["log"].append("⚙️ Scoring en cours...")
            run_lead_scoring()
            scrape_status["log"].append("✅ Scoring terminé")
        scrape_status["log"].append("🎉 Pipeline complet !")
    except Exception as e:
        scrape_status["log"].append(f"❌ Erreur : {str(e)}")
    finally:
        scrape_status["running"] = False


@router.post("/scrape/start")
def start_scrape(params: ScrapeParams):
    global scrape_status
    if scrape_status["running"]:
        raise HTTPException(status_code=409, detail="Un scraping est déjà en cours")
    scrape_status = {"running": True, "log": [], "done": 0, "total": 0}
    t = threading.Thread(target=_run_scrape, args=(params,), daemon=True)
    t.start()
    return {"status": "started"}


@router.get("/scrape/status")
def get_scrape_status():
    return scrape_status


@router.post("/scrape/stop")
def stop_scrape():
    scrape_status["running"] = False
    scrape_status["log"].append("⛔ Arrêté manuellement")
    return {"status": "stopped"}


@router.post("/scoring/run")
def run_scoring():
    """
    Lance le rescoring complet sur tous les prospects.
    Système 300 points : joignabilité (80) + identité (60) + potentiel (80) + signaux (80).
    Normalise à /100 pour stockage.
    """
    if scrape_status["running"]:
        raise HTTPException(status_code=409, detail="Un scraping est déjà en cours")

    try:
        scrape_status["running"] = True
        scrape_status["log"] = []
        scrape_status["log"].append("⚙️ Rescoring enrichi 300pts en cours...")
        run_lead_scoring()
        scrape_status["log"].append("✅ Rescoring terminé")
        scrape_status["running"] = False
        return {"status": "completed", "message": "Scoring enrichi exécuté"}
    except Exception as e:
        scrape_status["log"].append(f"❌ Erreur : {str(e)}")
        scrape_status["running"] = False
        raise HTTPException(status_code=500, detail=str(e))