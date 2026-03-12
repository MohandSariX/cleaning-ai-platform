from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Devis(Base):
    __tablename__ = "devis"

    id = Column(Integer, primary_key=True, index=True)

    client_id  = Column(Integer, ForeignKey("clients.id"), nullable=False)

    # Numéro devis : DEV-2024-001
    numero     = Column(String, unique=True)

    # Type de prestation
    # bureaux | fin_chantier | copropriete | autre
    service_type = Column(String)

    # Description du chantier
    description  = Column(Text)

    # Superficie en m²
    surface_m2   = Column(Float, nullable=True)

    # Fréquence (pour bureaux récurrents)
    # unique | hebdo | bihebdo | mensuel
    frequence    = Column(String, default="unique")

    # Montant HT
    montant_ht   = Column(Float, default=0)
    tva_pct      = Column(Float, default=20.0)

    @property
    def montant_ttc(self):
        return round(self.montant_ht * (1 + self.tva_pct / 100), 2)

    # Statut
    # brouillon | envoye | accepte | refuse | expire
    status       = Column(String, default="brouillon")

    notes        = Column(Text)

    # Timestamps
    created_at   = Column(DateTime, server_default=func.now())
    updated_at   = Column(DateTime, onupdate=func.now())
    sent_at      = Column(DateTime, nullable=True)
    responded_at = Column(DateTime, nullable=True)

    # Relations
    client   = relationship("Client",   back_populates="devis")
    chantier = relationship("Chantier", back_populates="devis", uselist=False)