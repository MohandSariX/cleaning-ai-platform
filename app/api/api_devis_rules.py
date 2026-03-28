"""
API Devis Rules — CRUD sur devis_rules.json depuis le dashboard.
"""
import json
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.utils.devis_engine import load_rules, RULES_PATH, get_all_tarifs

router = APIRouter()


@router.get("/devis-rules")
def get_rules():
    """Retourne toutes les règles tarifaires."""
    return load_rules()


@router.get("/devis-rules/tarifs")
def get_tarifs():
    """Retourne la liste des tarifs pour le dashboard."""
    return get_all_tarifs()


class TarifUpdate(BaseModel):
    tarif_m2: float | None = None
    tarif_horaire: float | None = None
    minimum_ht: float | None = None


@router.patch("/devis-rules/tarifs/{cle}")
def update_tarif(cle: str, update: TarifUpdate):
    """Met à jour un tarif spécifique."""
    rules = load_rules()
    if cle not in rules["tarifs"]:
        raise HTTPException(status_code=404, detail=f"Tarif '{cle}' introuvable")

    tarif = rules["tarifs"][cle]
    if update.tarif_m2 is not None:
        tarif["tarif_m2"] = update.tarif_m2
    if update.tarif_horaire is not None:
        tarif["tarif_horaire"] = update.tarif_horaire
    if update.minimum_ht is not None:
        tarif["minimum_ht"] = update.minimum_ht

    rules["_derniere_maj"] = __import__("datetime").datetime.now().strftime("%Y-%m-%d")

    with open(RULES_PATH, "w", encoding="utf-8") as f:
        json.dump(rules, f, ensure_ascii=False, indent=2)

    return {"status": "ok", "tarif": tarif}


class SocieteUpdate(BaseModel):
    nom: str | None = None
    gerant: str | None = None
    email: str | None = None
    telephone: str | None = None
    adresse: str | None = None
    siret: str | None = None
    numero_tva: str | None = None
    iban: str | None = None
    bic: str | None = None


@router.patch("/devis-rules/societe")
def update_societe(update: SocieteUpdate):
    """Met à jour les infos légales de la société."""
    rules = load_rules()
    societe = rules.get("societe", {})

    for field, value in update.dict(exclude_none=True).items():
        societe[field] = value

    rules["societe"] = societe
    rules["_derniere_maj"] = __import__("datetime").datetime.now().strftime("%Y-%m-%d")

    with open(RULES_PATH, "w", encoding="utf-8") as f:
        json.dump(rules, f, ensure_ascii=False, indent=2)

    return {"status": "ok", "societe": societe}


@router.post("/devis-rules/simulate")
def simulate_devis(type_prestation: str, superficie_m2: float, frequence: str):
    """Simule un calcul de devis avec les tarifs actuels."""
    from app.utils.devis_engine import calculate
    return calculate(type_prestation, superficie_m2, frequence)