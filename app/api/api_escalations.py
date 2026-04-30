from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.core.database import SessionLocal
from app.models.escalation import Escalation
from app.models.prospect import Prospect
from app.agents.chantier_auto import (
    process_escalation_decision,
    get_autonomy_config,
    process_accepted_devis,
)

router = APIRouter(prefix="/api/escalations", tags=["escalations"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Schemas ──────────────────────────────────────────────────────────────────

class EscalationResponse(BaseModel):
    id: int
    decision_type: str
    priority: str
    title: str
    description: str | None
    context_data: str | None
    status: str
    prospect_id: int | None
    prospect_name: str | None
    devis_id: int | None
    chantier_id: int | None
    amount_ht: float | None
    amount_ttc: float | None
    ia_recommendation: str | None
    ia_confidence: float | None
    ia_reasoning: str | None
    approved_by: str | None
    decision_note: str | None
    decided_at: datetime | None
    auto_resolve_at: datetime | None
    default_action: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class EscalationDecisionRequest(BaseModel):
    decision: str  # approve, reject
    approved_by: str
    note: str | None = None


class AutonomyConfigResponse(BaseModel):
    devis_auto_threshold_ht: float
    discount_auto_max_pct: float
    chantier_auto_planning: bool
    chantier_notification_client: bool
    planning_conflict_escalate: bool


class AutonomyConfigUpdate(BaseModel):
    devis_auto_threshold_ht: float | None = None
    discount_auto_max_pct: float | None = None
    chantier_auto_planning: bool | None = None
    chantier_notification_client: bool | None = None
    planning_conflict_escalate: bool | None = None


class EscalationStats(BaseModel):
    total: int
    pending: int
    approved: int
    rejected: int
    auto_resolved: int
    by_type: dict[str, int]
    by_priority: dict[str, int]


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/", response_model=List[EscalationResponse])
def list_escalations(
    status: Optional[str] = Query(None, description="pending, approved, rejected, auto_resolved"),
    decision_type: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
):
    """Liste les escalations avec filtres"""
    query = db.query(Escalation)

    if status:
        query = query.filter(Escalation.status == status)
    if decision_type:
        query = query.filter(Escalation.decision_type == decision_type)
    if priority:
        query = query.filter(Escalation.priority == priority)

    escalations = query.order_by(desc(Escalation.created_at)).limit(limit).all()

    # Enrichir avec prospect_name
    result = []
    for esc in escalations:
        data = EscalationResponse.model_validate(esc)
        if esc.prospect_id:
            prospect = db.query(Prospect).filter(Prospect.id == esc.prospect_id).first()
            if prospect:
                data.prospect_name = prospect.company_name
        result.append(data)

    return result


@router.get("/stats", response_model=EscalationStats)
def get_escalation_stats(db: Session = Depends(get_db)):
    """Statistiques sur les escalations"""
    all_escs = db.query(Escalation).all()

    by_type = {}
    by_priority = {}
    by_status = {"pending": 0, "approved": 0, "rejected": 0, "auto_resolved": 0}

    for esc in all_escs:
        by_type[esc.decision_type] = by_type.get(esc.decision_type, 0) + 1
        by_priority[esc.priority] = by_priority.get(esc.priority, 0) + 1
        by_status[esc.status] = by_status.get(esc.status, 0) + 1

    return EscalationStats(
        total=len(all_escs),
        pending=by_status["pending"],
        approved=by_status["approved"],
        rejected=by_status["rejected"],
        auto_resolved=by_status["auto_resolved"],
        by_type=by_type,
        by_priority=by_priority,
    )


@router.get("/{escalation_id}", response_model=EscalationResponse)
def get_escalation(escalation_id: int, db: Session = Depends(get_db)):
    """Détail d'une escalation"""
    esc = db.query(Escalation).filter(Escalation.id == escalation_id).first()
    if not esc:
        raise HTTPException(404, "Escalation not found")

    data = EscalationResponse.model_validate(esc)
    if esc.prospect_id:
        prospect = db.query(Prospect).filter(Prospect.id == esc.prospect_id).first()
        if prospect:
            data.prospect_name = prospect.company_name

    return data


@router.post("/{escalation_id}/decide")
def decide_escalation(
    escalation_id: int,
    decision: EscalationDecisionRequest,
    db: Session = Depends(get_db),
):
    """Prendre une décision sur une escalation (approve/reject)"""
    if decision.decision not in ["approve", "reject"]:
        raise HTTPException(400, "Decision must be 'approve' or 'reject'")

    try:
        process_escalation_decision(
            db=db,
            escalation_id=escalation_id,
            decision=decision.decision,
            approved_by=decision.approved_by,
            note=decision.note,
        )
        return {"status": "ok", "decision": decision.decision}
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, f"Error processing decision: {str(e)}")


@router.get("/config/autonomy", response_model=AutonomyConfigResponse)
def get_autonomy_config_endpoint(db: Session = Depends(get_db)):
    """Récupère la configuration d'autonomie de Claude"""
    config = get_autonomy_config(db)
    return AutonomyConfigResponse(**config)


@router.patch("/config/autonomy")
def update_autonomy_config(
    config: AutonomyConfigUpdate,
    db: Session = Depends(get_db),
):
    """
    Met à jour la configuration d'autonomie
    TODO: À terme, persister dans tenant_config JSON field
    """
    # Pour l'instant, on retourne juste la config mise à jour
    # Dans une vraie implémentation, on sauvegarderait dans tenant_config
    current = get_autonomy_config(db)

    updated = {**current}
    if config.devis_auto_threshold_ht is not None:
        updated["devis_auto_threshold_ht"] = config.devis_auto_threshold_ht
    if config.discount_auto_max_pct is not None:
        updated["discount_auto_max_pct"] = config.discount_auto_max_pct
    if config.chantier_auto_planning is not None:
        updated["chantier_auto_planning"] = config.chantier_auto_planning
    if config.chantier_notification_client is not None:
        updated["chantier_notification_client"] = config.chantier_notification_client
    if config.planning_conflict_escalate is not None:
        updated["planning_conflict_escalate"] = config.planning_conflict_escalate

    # TODO: Sauvegarder dans DB
    # tenant = get_tenant_by_email(db, "contact.proprexis@gmail.com")
    # tenant.config = json.dumps({"autonomy": updated})
    # db.commit()

    return {
        "status": "ok",
        "message": "Config mise à jour (TODO: persister en DB)",
        "config": updated,
    }


@router.post("/test/process-devis/{devis_id}")
def test_process_devis(devis_id: int, db: Session = Depends(get_db)):
    """Endpoint de test pour forcer le traitement d'un devis accepté"""
    result = process_accepted_devis(db, devis_id)
    return result
