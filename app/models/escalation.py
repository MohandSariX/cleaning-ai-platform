from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class Escalation(Base):
    __tablename__ = "escalations"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)

    # Type de décision
    decision_type = Column(String(50), nullable=False, index=True)  # devis_high_value, discount_request, planning_conflict, chantier_urgent
    priority = Column(String(20), default="medium")  # low, medium, high, critical

    # Contexte
    title = Column(String(200), nullable=False)
    description = Column(Text)
    context_data = Column(Text)  # JSON stringifié avec détails

    # Entités liées
    prospect_id = Column(Integer, ForeignKey("prospects.id"), nullable=True)
    devis_id = Column(Integer, nullable=True)
    chantier_id = Column(Integer, nullable=True)

    # Montants si applicable
    amount_ht = Column(Float, nullable=True)
    amount_ttc = Column(Float, nullable=True)

    # Statut décision
    status = Column(String(20), default="pending", index=True)  # pending, approved, rejected, auto_resolved
    approved_by = Column(String(100), nullable=True)
    decision_note = Column(Text, nullable=True)
    decided_at = Column(DateTime, nullable=True)

    # IA recommendation
    ia_recommendation = Column(String(20), nullable=True)  # approve, reject, review
    ia_confidence = Column(Float, nullable=True)  # 0-100
    ia_reasoning = Column(Text, nullable=True)

    # Auto-résolution
    auto_resolve_at = Column(DateTime, nullable=True)  # Si pas de réponse avant cette date, action par défaut
    default_action = Column(String(20), nullable=True)  # approve, reject

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    tenant = relationship("Tenant", back_populates="escalations")
    prospect = relationship("Prospect", foreign_keys=[prospect_id])

    def __repr__(self):
        return f"<Escalation {self.id} {self.decision_type} - {self.status}>"
