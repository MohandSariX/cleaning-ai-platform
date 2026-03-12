from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Facture(Base):
    __tablename__ = "factures"

    id = Column(Integer, primary_key=True, index=True)

    client_id   = Column(Integer, ForeignKey("clients.id"),   nullable=False)
    chantier_id = Column(Integer, ForeignKey("chantiers.id"), nullable=True)

    # Numéro facture : FAC-2024-001
    numero      = Column(String, unique=True)

    # Montants
    montant_ht  = Column(Float, default=0)
    tva_pct     = Column(Float, default=20.0)

    @property
    def montant_ttc(self):
        return round(self.montant_ht * (1 + self.tva_pct / 100), 2)

    # Statut
    # brouillon | envoyee | payee | en_retard | annulee
    status      = Column(String, default="brouillon")

    description = Column(Text)
    notes       = Column(Text)

    # Dates
    date_emission  = Column(Date, nullable=True)
    date_echeance  = Column(Date, nullable=True)   # Date limite de paiement
    date_paiement  = Column(Date, nullable=True)   # Date de paiement effectif

    # Timestamps
    created_at  = Column(DateTime, server_default=func.now())
    updated_at  = Column(DateTime, onupdate=func.now())

    # Relations
    client   = relationship("Client",   back_populates="factures")
    chantier = relationship("Chantier", back_populates="factures")