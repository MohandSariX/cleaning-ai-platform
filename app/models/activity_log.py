"""
Modèle ActivityLog — Journal d'activité centralisé de tous les agents.
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id          = Column(Integer, primary_key=True, index=True)

    # Type d'événement
    # email_sent | email_received | qualification | devis_sent | scraping
    # enrichment | system | error | decision | scheduler | watchdog
    event_type  = Column(String, nullable=False, index=True)

    # Sous-catégorie : prospection | relance | question | accuse | signature...
    event_sub   = Column(String, nullable=True)

    # Message principal affiché dans le journal
    message     = Column(Text, nullable=False)

    # Détails techniques (JSON)
    details_json = Column(Text, nullable=True)

    # Liens vers les entités concernées
    prospect_id = Column(Integer, ForeignKey("prospects.id"), nullable=True)
    client_id   = Column(Integer, ForeignKey("clients.id"), nullable=True)

    # Statut : success | warning | error | info
    status      = Column(String, default="info")

    # Métriques associées
    metric_value = Column(Float, nullable=True)  # ex: montant devis, score, nb prospects

    # Décision IA (pourquoi cette action)
    ia_decision  = Column(Text, nullable=True)

    # Timestamp
    created_at  = Column(DateTime, server_default=func.now(), index=True)

    # Relations
    prospect = relationship("Prospect", backref="activity_logs", foreign_keys=[prospect_id])