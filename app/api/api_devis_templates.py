from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.devis_template import DevisTemplate
from typing import Optional, List
from pydantic import BaseModel

router = APIRouter(prefix="/api/devis-templates", tags=["devis-templates"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Schemas ──────────────────────────────────────────────────

class DevisTemplateCreate(BaseModel):
    name: str
    category: Optional[str] = None
    type_prestation: Optional[str] = None
    description: Optional[str] = None
    template_json: dict
    variables_required: List[str] = []
    is_default: bool = False
    active: bool = True


class DevisTemplateUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    type_prestation: Optional[str] = None
    description: Optional[str] = None
    template_json: Optional[dict] = None
    variables_required: Optional[List[str]] = None
    is_default: Optional[bool] = None
    active: Optional[bool] = None


class DevisTemplateResponse(BaseModel):
    id: int
    name: str
    category: Optional[str]
    type_prestation: Optional[str]
    description: Optional[str]
    template_json: dict
    variables_required: List[str]
    is_default: bool
    active: bool
    created_at: str
    updated_at: Optional[str]

    model_config = {"from_attributes": True}


# ── Endpoints ────────────────────────────────────────────────

@router.get("/", response_model=List[DevisTemplateResponse])
def list_templates(
    db: Session = Depends(get_db),
    category: Optional[str] = None,
    type_prestation: Optional[str] = None,
    active_only: bool = True
):
    """Liste tous les templates avec filtres optionnels."""
    q = db.query(DevisTemplate)

    if active_only:
        q = q.filter(DevisTemplate.active == True)
    if category:
        q = q.filter(DevisTemplate.category == category)
    if type_prestation:
        q = q.filter(DevisTemplate.type_prestation == type_prestation)

    q = q.order_by(DevisTemplate.is_default.desc(), DevisTemplate.name)

    templates = q.all()
    return [_template_to_response(t) for t in templates]


@router.get("/{template_id}", response_model=DevisTemplateResponse)
def get_template(template_id: int, db: Session = Depends(get_db)):
    """Récupère un template par ID."""
    template = db.query(DevisTemplate).filter(DevisTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template introuvable")
    return _template_to_response(template)


@router.post("/", response_model=DevisTemplateResponse)
def create_template(data: DevisTemplateCreate, db: Session = Depends(get_db)):
    """Crée un nouveau template."""
    # Si is_default=True, désactiver les autres defaults pour cette catégorie/type
    if data.is_default:
        db.query(DevisTemplate).filter(
            DevisTemplate.category == data.category,
            DevisTemplate.type_prestation == data.type_prestation,
            DevisTemplate.is_default == True
        ).update({"is_default": False})

    template = DevisTemplate(**data.model_dump())
    db.add(template)
    db.commit()
    db.refresh(template)

    return _template_to_response(template)


@router.patch("/{template_id}", response_model=DevisTemplateResponse)
def update_template(
    template_id: int,
    data: DevisTemplateUpdate,
    db: Session = Depends(get_db)
):
    """Met à jour un template."""
    template = db.query(DevisTemplate).filter(DevisTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template introuvable")

    # Si on passe is_default=True, désactiver les autres
    if data.is_default:
        db.query(DevisTemplate).filter(
            DevisTemplate.category == template.category,
            DevisTemplate.type_prestation == template.type_prestation,
            DevisTemplate.is_default == True,
            DevisTemplate.id != template_id
        ).update({"is_default": False})

    # Mise à jour
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(template, key, value)

    db.commit()
    db.refresh(template)

    return _template_to_response(template)


@router.delete("/{template_id}")
def delete_template(template_id: int, db: Session = Depends(get_db)):
    """Supprime (soft delete) un template."""
    template = db.query(DevisTemplate).filter(DevisTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template introuvable")

    template.active = False
    db.commit()

    return {"status": "deleted", "id": template_id}


@router.post("/render")
def render_template(data: dict, db: Session = Depends(get_db)):
    """Rend un template avec des variables.

    Body: {
        "template_id": 1,
        "variables": {
            "client_name": "ABC Corp",
            "montant_ht": 5000,
            "description": "Nettoyage bureaux"
        }
    }
    """
    template_id = data.get("template_id")
    variables = data.get("variables", {})

    template = db.query(DevisTemplate).filter(DevisTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template introuvable")

    # Vérifier variables requises
    missing = [v for v in template.variables_required if v not in variables]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Variables manquantes: {', '.join(missing)}"
        )

    # Rendu du template
    rendered = _render_template_json(template.template_json, variables)

    return {
        "template_id": template.id,
        "template_name": template.name,
        "rendered": rendered,
        "variables_used": variables
    }


# ── Helpers ──────────────────────────────────────────────────

def _template_to_response(t: DevisTemplate) -> dict:
    return {
        "id": t.id,
        "name": t.name,
        "category": t.category,
        "type_prestation": t.type_prestation,
        "description": t.description,
        "template_json": t.template_json,
        "variables_required": t.variables_required,
        "is_default": t.is_default,
        "active": t.active,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "updated_at": t.updated_at.isoformat() if t.updated_at else None,
    }


def _render_template_json(template_json: dict, variables: dict) -> dict:
    """Remplace les variables {{var}} dans le template JSON."""
    import json
    import re

    # Convertir en string pour faire les remplacements
    template_str = json.dumps(template_json)

    # Remplacer chaque variable
    for key, value in variables.items():
        pattern = r'\{\{' + key + r'\}\}'
        template_str = re.sub(pattern, str(value), template_str)

    # Reconvertir en dict
    return json.loads(template_str)
