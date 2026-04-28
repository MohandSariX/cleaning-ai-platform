"""
Modèles pour Claude l'associée IA — Mémoire persistante et décisions
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.core.database import Base


class AIMemory(Base):
    """
    Mémoire persistante de Claude — patterns, stratégies, apprentissages

    Exemples :
    - best_email_time_syndic_94 → "10:00-11:00"
    - objection_prix_trop_cher → "Insister qualité + garantie. Proposer -5% si engagement 6 mois"
    - template_email_btp_efficace → "Modèle avec taux réponse 12%..."
    """
    __tablename__ = "ai_memory"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(255), unique=True, nullable=False, index=True)
    value = Column(Text)
    context = Column(String(100), index=True)  # "prospection", "commercial", "strategy", "learning"
    meta_data = Column(JSONB)  # Données structurées (taux succès, sample size, dates...)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())


class AIDecision(Base):
    """
    Journal des décisions autonomes de Claude — traçabilité et apprentissage

    Types de décisions :
    - email_sent : envoi email prospection
    - devis_generated : génération devis
    - prospect_enriched : enrichissement Pappers
    - price_negotiated : négociation prix
    - campaign_adjusted : ajustement timing/ciblage
    """
    __tablename__ = "ai_decisions"

    id = Column(Integer, primary_key=True, index=True)
    decision_type = Column(String(100), index=True)
    decision_data = Column(JSONB)  # Données complètes de la décision
    reasoning = Column(Text)  # Explication du raisonnement
    outcome = Column(String(50), default="pending")  # pending, success, failed, cancelled
    escalated_to_human = Column(Boolean, default=False)
    human_feedback = Column(Text, nullable=True)  # Retour de Mohand si escaladé
    created_at = Column(DateTime, server_default=func.now(), index=True)


class ConversationHistory(Base):
    """
    Historique des conversations Telegram avec Claude
    Pour contexte long terme et amélioration continue
    """
    __tablename__ = "conversation_history"

    id = Column(Integer, primary_key=True, index=True)
    message_from = Column(String(50))  # "mohand" ou "claude"
    message_text = Column(Text)
    context = Column(JSONB)  # Contexte CRM au moment du message
    created_at = Column(DateTime, server_default=func.now(), index=True)
