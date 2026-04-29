"""
API Devis Rules — CRUD sur devis_rules.json depuis le dashboard.
DEPRECATED: Utilisez /api/products à la place.
Conservé temporairement pour compatibilité avec le dashboard.
"""
import json
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.utils.devis_engine import load_rules, get_all_tarifs

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
    """
    DEPRECATED: Utilisez PATCH /api/products/{id} à la place.
    Met à jour un tarif spécifique.
    """
    raise HTTPException(
        status_code=410,
        detail="Endpoint déprécié. Utilisez PATCH /api/products/{id} à la place. "
               "Les tarifs sont maintenant stockés en base de données (table products)."
    )


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
    """
    DEPRECATED: Les infos société sont maintenant stockées dans la table tenants.
    Met à jour les infos légales de la société.
    """
    raise HTTPException(
        status_code=410,
        detail="Endpoint déprécié. Les informations société sont maintenant stockées "
               "dans la table tenants (TenantConfig)."
    )


@router.post("/devis-rules/simulate")
def simulate_devis(type_prestation: str, superficie_m2: float, frequence: str):
    """Simule un calcul de devis avec les tarifs actuels."""
    from app.utils.devis_engine import calculate
    return calculate(type_prestation, superficie_m2, frequence)