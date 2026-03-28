"""
Modèle Conversation — Persistance des échanges de qualification en PostgreSQL.
Remplace le dict en mémoire `conversations` dans qualification_agent.py
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id          = Column(Integer, primary_key=True, index=True)
    prospect_id = Column(Integer, ForeignKey("prospects.id"), nullable=False, unique=True)
    email       = Column(String, nullable=False, index=True)

    # Statut : en_cours | devis_envoye | signe | perdu | en_attente
    status      = Column(String, default="en_cours")

    # Infos collectées durant la qualification (JSON stocké en Text)
    infos_json  = Column(Text, default="{}")

    # Historique des échanges (JSON liste)
    historique_json = Column(Text, default="[]")

    # Compteur d'échanges
    nb_echanges = Column(Integer, default=0)

    # Timestamps
    created_at  = Column(DateTime, server_default=func.now())
    updated_at  = Column(DateTime, onupdate=func.now())
    devis_envoye_at = Column(DateTime, nullable=True)

    # Relation
    prospect = relationship("Prospect", backref="conversation")