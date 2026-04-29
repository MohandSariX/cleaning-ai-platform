"""
API Escalations — Décisions nécessitant validation Mohand
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime
from app.core.database import SessionLocal
from app.models.ai_memory import AIDecision
from app.models.devis import Devis
from app.models.prospect import Prospect


router = APIRouter(prefix="/api/escalations", tags=["escalations"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class EscalationApproval(BaseModel):
    approved: bool
    notes: Optional[str] = None


@router.get("/")
def list_escalations(db: Session = Depends(get_db)):
    """
    Liste toutes les décisions en attente de validation.

    Retourne les escalations depuis AIDecision table avec status='escalated'.
    """
    escalations = db.query(AIDecision).filter(
        AIDecision.decision_type == "escalation",
        AIDecision.metadata.contains({"status": "pending"})
    ).order_by(AIDecision.timestamp.desc()).all()

    result = []
    for esc in escalations:
        metadata = esc.metadata or {}

        escalation_data = {
            "id": esc.id,
            "timestamp": esc.timestamp.isoformat(),
            "reason": esc.reasoning,
            "type": metadata.get("escalation_type", "unknown"),
            "details": metadata,
        }

        # Enrichir avec les données liées
        if metadata.get("devis_id"):
            devis = db.query(Devis).filter(Devis.id == metadata["devis_id"]).first()
            if devis:
                escalation_data["devis"] = {
                    "id": devis.id,
                    "montant_ttc": devis.montant_ttc,
                    "prospect_id": devis.prospect_id
                }
                prospect = db.query(Prospect).filter(Prospect.id == devis.prospect_id).first()
                if prospect:
                    escalation_data["prospect"] = {
                        "company_name": prospect.company_name,
                        "city": prospect.city
                    }

        result.append(escalation_data)

    return {"escalations": result, "count": len(result)}


@router.post("/{escalation_id}/approve")
def approve_escalation(
    escalation_id: int,
    data: EscalationApproval,
    db: Session = Depends(get_db)
):
    """
    Approuve ou refuse une escalation.

    Args:
        escalation_id: ID de l'escalation
        data: {approved: true/false, notes: "..."}
    """
    escalation = db.query(AIDecision).filter(AIDecision.id == escalation_id).first()

    if not escalation:
        raise HTTPException(status_code=404, detail="Escalation introuvable")

    # Mettre à jour le metadata
    metadata = escalation.metadata or {}
    metadata["status"] = "approved" if data.approved else "rejected"
    metadata["approved_at"] = datetime.now().isoformat()
    metadata["approval_notes"] = data.notes

    escalation.metadata = metadata
    db.commit()

    # TODO: Exécuter l'action approuvée (envoyer devis, accepter négociation, etc.)
    # Pour l'instant, juste marquer comme traité

    return {
        "success": True,
        "escalation_id": escalation_id,
        "approved": data.approved,
        "message": "Escalation approuvée" if data.approved else "Escalation refusée"
    }


@router.get("/stats")
def escalations_stats(db: Session = Depends(get_db)):
    """
    Statistiques sur les escalations.
    """
    total = db.query(AIDecision).filter(
        AIDecision.decision_type == "escalation"
    ).count()

    pending = db.query(AIDecision).filter(
        AIDecision.decision_type == "escalation",
        AIDecision.metadata.contains({"status": "pending"})
    ).count()

    approved = db.query(AIDecision).filter(
        AIDecision.decision_type == "escalation",
        AIDecision.metadata.contains({"status": "approved"})
    ).count()

    rejected = db.query(AIDecision).filter(
        AIDecision.decision_type == "escalation",
        AIDecision.metadata.contains({"status": "rejected"})
    ).count()

    return {
        "total": total,
        "pending": pending,
        "approved": approved,
        "rejected": rejected,
        "approval_rate": round((approved / total * 100), 1) if total > 0 else 0
    }
