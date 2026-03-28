"""
Modèle EmailLog — Suivi complet de tous les emails envoyés.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class EmailLog(Base):
    __tablename__ = "email_logs"

    id          = Column(Integer, primary_key=True, index=True)
    prospect_id = Column(Integer, ForeignKey("prospects.id"), nullable=False)

    # Type : prospection | relance | qualification | devis
    email_type  = Column(String, default="prospection")

    recipient   = Column(String)
    subject     = Column(String)
    body        = Column(Text, nullable=True)

    # Statut : sent | failed | bounced | opened | replied
    status      = Column(String, default="sent")

    sent_at     = Column(DateTime, server_default=func.now())
    opened_at   = Column(DateTime, nullable=True)
    replied_at  = Column(DateTime, nullable=True)

    # Relation
    prospect = relationship("Prospect", backref="email_logs")