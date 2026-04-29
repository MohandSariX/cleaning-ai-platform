"""
API Tenants — Configuration tenant (infos société)
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from app.core.database import SessionLocal
from app.models.tenant import Tenant, TenantConfig, get_tenant_by_id, get_tenant_by_email
from sqlalchemy.orm import Session


router = APIRouter(prefix="/api/tenants", tags=["tenants"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ══════════════════════════════════════════════════════════════
#  SCHEMAS
# ══════════════════════════════════════════════════════════════

class SocieteInfo(BaseModel):
    """Informations société pour compatibilité frontend."""
    nom: str
    forme_juridique: Optional[str] = ""
    gerant: Optional[str] = ""
    email: str
    telephone: Optional[str] = ""
    adresse: Optional[str] = ""
    siret: Optional[str] = ""
    numero_tva: Optional[str] = ""
    iban: Optional[str] = ""
    bic: Optional[str] = ""


class SocieteUpdate(BaseModel):
    """Mise à jour infos société."""
    nom: Optional[str] = None
    forme_juridique: Optional[str] = None
    gerant: Optional[str] = None
    email: Optional[str] = None
    telephone: Optional[str] = None
    adresse: Optional[str] = None
    siret: Optional[str] = None
    numero_tva: Optional[str] = None
    iban: Optional[str] = None
    bic: Optional[str] = None


# ══════════════════════════════════════════════════════════════
#  ENDPOINTS
# ══════════════════════════════════════════════════════════════

@router.get("/owner/config", response_model=SocieteInfo)
def get_owner_config(db: Session = Depends(get_db)):
    """
    Récupère la configuration du tenant owner (infos société).
    Retourne un format compatible avec l'ancien endpoint /devis-rules/societe.
    """
    owner = get_tenant_by_email(db, "contact.proprexis@gmail.com")
    if not owner:
        raise HTTPException(status_code=404, detail="Tenant owner introuvable")

    return SocieteInfo(
        nom=owner.name,
        forme_juridique="Auto-entrepreneur",
        gerant="Mohand Sari",
        email=owner.email,
        telephone="06 XX XX XX XX",
        adresse="Champigny-sur-Marne, 94500",
        siret="XXX XXX XXX XXXXX",
        numero_tva="FR XX XXX XXX XXX",
        iban="FR76 XXXX XXXX XXXX XXXX XXXX XXX",
        bic="XXXXXXXX"
    )


@router.get("/{tenant_id}/config", response_model=SocieteInfo)
def get_tenant_config(tenant_id: int, db: Session = Depends(get_db)):
    """
    Récupère la configuration d'un tenant par ID.
    """
    tenant = get_tenant_by_id(db, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant introuvable")

    return SocieteInfo(
        nom=tenant.name,
        forme_juridique="Auto-entrepreneur",
        gerant="Mohand Sari",
        email=tenant.email,
        telephone="06 XX XX XX XX",
        adresse="Champigny-sur-Marne, 94500",
        siret="XXX XXX XXX XXXXX",
        numero_tva="FR XX XXX XXX XXX",
        iban="FR76 XXXX XXXX XXXX XXXX XXXX XXX",
        bic="XXXXXXXX"
    )


@router.patch("/owner/config", response_model=SocieteInfo)
def update_owner_config(data: SocieteUpdate, db: Session = Depends(get_db)):
    """
    Raccourci pour mettre à jour la config du tenant owner.
    """
    owner = get_tenant_by_email(db, "contact.proprexis@gmail.com")
    if not owner:
        raise HTTPException(status_code=404, detail="Tenant owner introuvable")

    # Mettre à jour les champs stockés dans Tenant
    if data.nom is not None:
        owner.name = data.nom
    if data.email is not None:
        owner.email = data.email

    db.commit()
    db.refresh(owner)

    return SocieteInfo(
        nom=owner.name,
        forme_juridique="Auto-entrepreneur",
        gerant="Mohand Sari",
        email=owner.email,
        telephone="06 XX XX XX XX",
        adresse="Champigny-sur-Marne, 94500",
        siret="XXX XXX XXX XXXXX",
        numero_tva="FR XX XXX XXX XXX",
        iban="FR76 XXXX XXXX XXXX XXXX XXXX XXX",
        bic="XXXXXXXX"
    )
