"""
API Pappers — endpoints pour l'enrichissement des prospects.
"""
from fastapi import APIRouter
from app.agents.pappers_agent import enrich_prospect, enrich_batch
import threading

router = APIRouter()


@router.post("/pappers/enrich/{prospect_id}")
def enrich_one(prospect_id: int):
    """Enrichit un prospect spécifique avec Pappers."""
    return enrich_prospect(prospect_id)


@router.post("/pappers/enrich-batch")
def enrich_batch_now(limit: int = 10):
    """Lance l'enrichissement batch en arrière-plan."""
    t = threading.Thread(target=enrich_batch, args=(limit,), daemon=True)
    t.start()
    return {"status": "started", "message": f"Enrichissement de {limit} prospects lancé"}


@router.post("/pappers/search")
def search(company_name: str, city: str = None):
    """Recherche une entreprise sur Pappers (test)."""
    from app.agents.pappers_agent import search_entreprise, extract_enrichment
    data = search_entreprise(company_name, city)
    if not data:
        return {"status": "not_found"}
    return {"status": "found", "data": extract_enrichment(data)}