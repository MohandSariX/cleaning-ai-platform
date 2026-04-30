"""
Agent autonome de gestion des chantiers
Crée, planifie et suit les chantiers automatiquement après acceptation devis
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import json

from app.core.database import SessionLocal
from app.models.devis import Devis
from app.models.chantier import Chantier
from app.models.prospect import Prospect
from app.models.escalation import Escalation
from app.agents.activity_logger import (
    log_system,
    log_claude_decision, log_claude_escalation
)


def get_autonomy_config(db: Session) -> dict:
    """Récupère la config d'autonomie depuis tenant_config ou valeurs par défaut"""
    # TODO: À terme, stocker dans tenant_config JSON field
    return {
        "devis_auto_threshold_ht": 10000,  # Devis <10k€ → auto, ≥10k€ → escalation
        "discount_auto_max_pct": 15,       # Discount <15% → auto, ≥15% → escalation
        "chantier_auto_planning": True,    # Claude peut planifier automatiquement
        "chantier_notification_client": True,  # Envoyer email confirmation au client
        "planning_conflict_escalate": True,    # Escalader si conflit détecté
    }


def create_escalation(
    db: Session,
    tenant_id: int,
    decision_type: str,
    title: str,
    description: str,
    priority: str = "medium",
    prospect_id: int = None,
    devis_id: int = None,
    chantier_id: int = None,
    amount_ht: float = None,
    amount_ttc: float = None,
    context_data: dict = None,
    ia_recommendation: str = None,
    ia_confidence: float = None,
    ia_reasoning: str = None,
    auto_resolve_hours: int = None,
    default_action: str = None,
) -> Escalation:
    """Crée une escalation pour validation humaine"""
    escalation = Escalation(
        tenant_id=tenant_id,
        decision_type=decision_type,
        priority=priority,
        title=title,
        description=description,
        context_data=json.dumps(context_data) if context_data else None,
        prospect_id=prospect_id,
        devis_id=devis_id,
        chantier_id=chantier_id,
        amount_ht=amount_ht,
        amount_ttc=amount_ttc,
        ia_recommendation=ia_recommendation,
        ia_confidence=ia_confidence,
        ia_reasoning=ia_reasoning,
        default_action=default_action,
    )

    if auto_resolve_hours:
        escalation.auto_resolve_at = datetime.utcnow() + timedelta(hours=auto_resolve_hours)

    db.add(escalation)
    db.commit()
    db.refresh(escalation)

    log_claude_escalation(
        reason=title,
        context={"escalation_id": escalation.id, "decision_type": decision_type, **(context_data or {})},
        priority=priority,
        details={"ia_recommendation": ia_recommendation, "ia_confidence": ia_confidence}
    )

    return escalation


def check_devis_need_escalation(db: Session, devis: Devis, config: dict) -> tuple[bool, str]:
    """Vérifie si un devis nécessite une escalation"""
    # Montant élevé
    if devis.montant_ht >= config["devis_auto_threshold_ht"]:
        return True, f"Montant élevé : {devis.montant_ht:.2f} € HT ≥ {config['devis_auto_threshold_ht']} € HT"

    # TODO: Ajouter checks discount si ajouté dans le modèle
    # if devis.discount_pct and devis.discount_pct >= config["discount_auto_max_pct"]:
    #     return True, f"Remise importante : {devis.discount_pct}% ≥ {config['discount_auto_max_pct']}%"

    return False, "OK pour traitement automatique"


def process_accepted_devis(db: Session, devis_id: int) -> dict:
    """
    Traite un devis accepté : crée le chantier automatiquement ou escalade
    Appelé par webhook ou job quotidien
    """
    devis = db.query(Devis).filter(Devis.id == devis_id).first()
    if not devis or devis.status != "accepte":
        return {"status": "skipped", "reason": "Devis non accepté"}

    config = get_autonomy_config(db)

    # Check si escalation nécessaire
    needs_escalation, reason = check_devis_need_escalation(db, devis, config)

    if needs_escalation:
        # Créer escalation
        escalation = create_escalation(
            db=db,
            tenant_id=devis.tenant_id,
            decision_type="devis_high_value",
            title=f"Validation devis {devis.numero} — {devis.montant_ttc:.0f} € TTC",
            description=f"Devis accepté par {devis.client_name}. {reason}",
            priority="high",
            devis_id=devis.id,
            amount_ht=devis.montant_ht,
            amount_ttc=devis.montant_ttc,
            context_data={
                "devis_numero": devis.numero,
                "client_name": devis.client_name,
                "service_type": devis.service_type,
                "frequence": devis.frequence,
            },
            ia_recommendation="approve",
            ia_confidence=85.0,
            ia_reasoning=f"Devis conforme. Client fiable. {reason}. Recommande approbation avec vérification.",
            auto_resolve_hours=48,  # Auto-approve dans 48h si pas de réponse
            default_action="approve",
        )

        return {
            "status": "escalated",
            "escalation_id": escalation.id,
            "reason": reason,
        }

    # Pas d'escalation → création automatique du chantier
    chantier = auto_create_chantier_from_devis(db, devis, config)

    return {
        "status": "auto_created",
        "chantier_id": chantier.id,
        "reason": "Création automatique (montant < seuil)",
    }


def auto_create_chantier_from_devis(db: Session, devis: Devis, config: dict) -> Chantier:
    """Crée automatiquement un chantier depuis un devis accepté"""
    # Estimer date début : J+7 par défaut
    date_debut = datetime.utcnow() + timedelta(days=7)

    # Estimer durée selon type et surface (logique simple)
    duree_heures = estimate_duration(devis.service_type, devis.description)

    chantier = Chantier(
        tenant_id=devis.tenant_id,
        client_id=devis.client_id,
        devis_id=devis.id,
        titre=f"{devis.service_type.replace('_', ' ').title()} — {devis.client_name}",
        type=devis.service_type,
        adresse=None,  # TODO: récupérer depuis client
        ville=None,
        date_debut=date_debut.date(),
        heure_debut="09:00",
        duree_heures=duree_heures,
        status="planifie",
        recurrence=devis.frequence if devis.frequence != "unique" else "unique",
        notes=f"Chantier créé automatiquement depuis devis {devis.numero}",
    )

    db.add(chantier)
    db.commit()
    db.refresh(chantier)

    log_system(
        message=f"Chantier #{chantier.id} créé automatiquement pour {devis.client_name}",
        status="success",
        details={
            "auto_created": True,
            "from_devis": devis.numero,
            "chantier_id": chantier.id,
            "type": chantier.type,
            "estimated_duration": duree_heures,
        }
    )

    log_claude_decision(
        decision_type="chantier_auto_create",
        action_taken="approved",
        reasoning=f"Devis {devis.numero} accepté, montant {devis.montant_ht:.0f} € HT < seuil. Création auto chantier.",
        confidence_score=95.0,
        outcome="Chantier créé automatiquement",
        details={
            "devis_id": devis.id,
            "chantier_id": chantier.id,
            "date_debut": date_debut.isoformat(),
        }
    )

    # TODO: Envoyer email de confirmation au client si config activée
    # if config["chantier_notification_client"]:
    #     send_chantier_confirmation_email(db, chantier)

    return chantier


def estimate_duration(service_type: str, description: str = None) -> float:
    """Estime la durée d'un chantier en heures selon le type"""
    base_durations = {
        "bureaux": 4.0,
        "fin_chantier": 6.0,
        "copropriete": 3.0,
        "vitrerie": 2.0,
        "autre": 4.0,
    }
    return base_durations.get(service_type, 4.0)


def run_chantier_auto_check():
    """
    Job quotidien : vérifie les devis acceptés et crée les chantiers
    À appeler depuis scheduler
    """
    db = SessionLocal()
    try:
        # Trouver tous les devis acceptés sans chantier associé
        devis_acceptes = db.query(Devis).filter(
            and_(
                Devis.status == "accepte",
                ~Devis.chantiers.any()  # Pas de chantier lié
            )
        ).all()

        results = {
            "total": len(devis_acceptes),
            "auto_created": 0,
            "escalated": 0,
            "errors": 0,
        }

        for devis in devis_acceptes:
            try:
                result = process_accepted_devis(db, devis.id)
                if result["status"] == "auto_created":
                    results["auto_created"] += 1
                elif result["status"] == "escalated":
                    results["escalated"] += 1
            except Exception as e:
                results["errors"] += 1
                print(f"Erreur traitement devis {devis.id}: {e}")

        print(f"[ChantierAuto] {results['total']} devis traités : {results['auto_created']} créés auto, {results['escalated']} escaladés, {results['errors']} erreurs")
        return results

    finally:
        db.close()


def process_escalation_decision(db: Session, escalation_id: int, decision: str, approved_by: str, note: str = None):
    """Traite la décision humaine sur une escalation"""
    escalation = db.query(Escalation).filter(Escalation.id == escalation_id).first()
    if not escalation:
        raise ValueError(f"Escalation {escalation_id} not found")

    escalation.status = "approved" if decision == "approve" else "rejected"
    escalation.approved_by = approved_by
    escalation.decision_note = note
    escalation.decided_at = datetime.utcnow()
    db.commit()

    # Si approuvé et c'est un devis → créer le chantier
    if decision == "approve" and escalation.decision_type == "devis_high_value" and escalation.devis_id:
        devis = db.query(Devis).filter(Devis.id == escalation.devis_id).first()
        if devis:
            config = get_autonomy_config(db)
            chantier = auto_create_chantier_from_devis(db, devis, config)
            escalation.chantier_id = chantier.id
            db.commit()

    log_claude_decision(
        decision_type=escalation.decision_type,
        action_taken=decision,
        reasoning=f"Décision humaine par {approved_by}: {decision}. Note: {note or 'N/A'}",
        confidence_score=100.0,
        outcome=f"Escalation {decision}",
        details={
            "escalation_id": escalation.id,
            "decision_note": note,
            "approved_by": approved_by,
        }
    )
