"""
Agent Pappers — Enrichissement des prospects via l'API Pappers.fr
Récupère : dirigeant, SIRET, CA, effectifs, date création, forme juridique
"""

import os
import requests
import logging
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.prospect import Prospect
from app.agents.telegram_notifier import send_message as tg

logger = logging.getLogger("proprexis.pappers")

PAPPERS_API_KEY = os.getenv("PAPPERS_API_KEY")
PAPPERS_URL = "https://api.pappers.fr/v2"


def search_entreprise(company_name: str, city: str = None) -> dict | None:
    """
    Cherche une entreprise sur Pappers par nom et ville.
    Retourne les données brutes ou None.
    """
    if not PAPPERS_API_KEY:
        logger.error("PAPPERS_API_KEY manquante dans .env")
        return None

    params = {
        "api_token": PAPPERS_API_KEY,
        "q": company_name,
        "par_page": 1,
    }
    if city:
        params["ville"] = city

    try:
        res = requests.get(f"{PAPPERS_URL}/recherche", params=params, timeout=10)
        data = res.json()
        resultats = data.get("resultats", [])
        if not resultats:
            return None
        return resultats[0]
    except Exception as e:
        logger.error(f"Pappers search erreur : {e}")
        return None


def get_entreprise_details(siren: str) -> dict | None:
    """
    Récupère les détails complets d'une entreprise par SIREN.
    """
    try:
        res = requests.get(
            f"{PAPPERS_URL}/entreprise",
            params={"api_token": PAPPERS_API_KEY, "siren": siren},
            timeout=10
        )
        return res.json()
    except Exception as e:
        logger.error(f"Pappers details erreur : {e}")
        return None


def extract_enrichment(data: dict) -> dict:
    """
    Extrait les infos utiles depuis la réponse Pappers.
    Retourne un dict propre pour mettre à jour le prospect.
    """
    enrichment = {}

    # Dirigeant principal
    dirigeants = data.get("dirigeants", [])
    if dirigeants:
        d = dirigeants[0]
        prenom = d.get("prenom", "")
        nom = d.get("nom", "")
        qualite = d.get("qualite", "")
        if nom:
            enrichment["dirigeant_nom"] = f"{prenom} {nom}".strip()
            enrichment["dirigeant_qualite"] = qualite

    # SIRET siège
    siege = data.get("siege", {})
    if siege.get("siret"):
        enrichment["siret"] = siege["siret"]

    # Chiffre d'affaires (dernier bilan)
    finances = data.get("finances", [])
    if finances:
        last = finances[0]
        ca = last.get("chiffre_affaires")
        if ca:
            enrichment["chiffre_affaires"] = ca
            # Catégorie CA
            if ca < 100_000:
                enrichment["ca_label"] = "Micro"
            elif ca < 500_000:
                enrichment["ca_label"] = "Petite"
            elif ca < 2_000_000:
                enrichment["ca_label"] = "Moyenne"
            elif ca < 10_000_000:
                enrichment["ca_label"] = "ETI"
            else:
                enrichment["ca_label"] = "Grande"

        effectif = last.get("effectifs_consolides") or last.get("effectif")
        if effectif:
            enrichment["effectifs"] = effectif

    # Date création
    date_creation = data.get("date_creation")
    if date_creation:
        enrichment["date_creation"] = date_creation

    # Forme juridique
    forme = data.get("forme_juridique")
    if forme:
        enrichment["forme_juridique"] = forme

    # Code NAF / APE
    code_naf = data.get("code_naf") or siege.get("code_naf")
    libelle_naf = data.get("libelle_naf") or siege.get("libelle_naf")
    if code_naf:
        enrichment["code_naf"] = code_naf
    if libelle_naf:
        enrichment["libelle_naf"] = libelle_naf

    # Statut actif
    statut = data.get("statut")
    enrichment["statut_juridique"] = statut

    return enrichment


def enrich_prospect(prospect_id: int) -> dict:
    """
    Enrichit un prospect spécifique avec les données Pappers.
    Retourne le résumé de l'enrichissement.
    """
    db = SessionLocal()
    try:
        prospect = db.query(Prospect).filter(Prospect.id == prospect_id).first()
        if not prospect:
            return {"status": "error", "message": "Prospect introuvable"}

        logger.info(f"Enrichissement Pappers : {prospect.company_name}")

        # Recherche
        data = search_entreprise(prospect.company_name, prospect.city)
        if not data:
            return {"status": "not_found", "message": f"{prospect.company_name} introuvable sur Pappers"}

        # Détails complets via SIREN
        siren = data.get("siren")
        if siren:
            details = get_entreprise_details(siren)
            if details:
                data = details

        # Extraire les infos utiles
        enrichment = extract_enrichment(data)
        if not enrichment:
            return {"status": "empty", "message": "Aucune info utile trouvée"}

        # Sauvegarder dans les notes du prospect (JSON enrichi)
        import json
        existing_notes = {}
        try:
            if prospect.score_explanation and "pappers" in prospect.score_explanation:
                pass
        except Exception:
            pass

        # Stocker dans score_explanation (on ajoute les infos Pappers)
        pappers_summary = []
        if enrichment.get("dirigeant_nom"):
            pappers_summary.append(f"Dirigeant : {enrichment['dirigeant_nom']} ({enrichment.get('dirigeant_qualite', '')})")
        if enrichment.get("chiffre_affaires"):
            ca = enrichment["chiffre_affaires"]
            pappers_summary.append(f"CA : {ca:,} € ({enrichment.get('ca_label', '')})")
        if enrichment.get("effectifs"):
            pappers_summary.append(f"Effectifs : {enrichment['effectifs']} salariés")
        if enrichment.get("date_creation"):
            pappers_summary.append(f"Créée en : {enrichment['date_creation'][:4]}")
        if enrichment.get("forme_juridique"):
            pappers_summary.append(f"Forme : {enrichment['forme_juridique']}")
        if enrichment.get("siret"):
            pappers_summary.append(f"SIRET : {enrichment['siret']}")

        # Ajouter au score_explanation existant
        existing = prospect.score_explanation or ""
        pappers_block = "\n\n--- Pappers ---\n" + "\n".join(pappers_summary)
        if "--- Pappers ---" in existing:
            # Remplacer le bloc existant
            parts = existing.split("--- Pappers ---")
            prospect.score_explanation = parts[0].rstrip() + pappers_block
        else:
            prospect.score_explanation = existing + pappers_block

        # Enrichir le score si CA connu
        if enrichment.get("chiffre_affaires"):
            ca = enrichment["chiffre_affaires"]
            bonus = 0
            if ca > 1_000_000: bonus = 15
            elif ca > 500_000: bonus = 10
            elif ca > 100_000: bonus = 5
            prospect.lead_score = min(100, (prospect.lead_score or 0) + bonus)

        db.commit()

        logger.info(f"✅ {prospect.company_name} enrichi — {len(pappers_summary)} infos")
        return {
            "status": "success",
            "prospect": prospect.company_name,
            "enrichment": enrichment,
            "summary": pappers_summary,
        }

    except Exception as e:
        logger.error(f"Erreur enrichissement {prospect_id} : {e}")
        db.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


def enrich_batch(limit: int = 10) -> dict:
    """
    Enrichit les N prochains prospects non encore enrichis.
    Appelé quotidiennement par le scheduler.
    """
    db = SessionLocal()
    try:
        # Prospects scorés sans enrichissement Pappers
        prospects = db.query(Prospect).filter(
            Prospect.lead_score >= 60,
            Prospect.score_explanation.notlike("%Pappers%"),
            Prospect.status.in_(["scored", "email_generated", "contacted"])
        ).order_by(Prospect.lead_score.desc()).limit(limit).all()

        if not prospects:
            return {"status": "empty", "enriched": 0}

        enriched = 0
        not_found = 0

        for prospect in prospects:
            result = enrich_prospect(prospect.id)
            if result["status"] == "success":
                enriched += 1
            else:
                not_found += 1

        logger.info(f"Batch Pappers : {enriched} enrichis, {not_found} introuvables")

        if enriched > 0:
            tg(f"📊 *Enrichissement Pappers terminé*\n{enriched} prospects enrichis avec CA + dirigeant")

        return {"status": "done", "enriched": enriched, "not_found": not_found}

    finally:
        db.close()