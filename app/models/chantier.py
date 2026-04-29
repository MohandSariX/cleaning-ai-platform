from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Chantier(Base):
    __tablename__ = "chantiers"

    id = Column(Integer, primary_key=True, index=True)
    # Multi-tenant
    tenant_id = Column(Integer, ForeignKey('tenants.id', ondelete='CASCADE'), nullable=True, index=True)


    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    devis_id  = Column(Integer, ForeignKey("devis.id"),   nullable=True)

    # Intitulé du chantier
    titre     = Column(String, nullable=False)

    # Type : bureaux | fin_chantier | copropriete | autre
    type      = Column(String, default="bureaux")

    # Adresse du chantier (peut différer de l'adresse client)
    adresse   = Column(String)
    ville     = Column(String)

    # Superficie
    surface_m2 = Column(Float, nullable=True)

    # Dates
    date_debut  = Column(Date, nullable=True)
    date_fin    = Column(Date, nullable=True)

    # Heure d'intervention (ex: "08:00")
    heure_debut = Column(String, nullable=True)
    duree_heures = Column(Float, nullable=True)

    # Statut
    # planifie | en_cours | termine | annule
    status    = Column(String, default="planifie")

    # Récurrence
    # unique | hebdo | bihebdo | mensuel
    recurrence = Column(String, default="unique")

    notes     = Column(Text)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # Relations
    client  = relationship("Client", back_populates="chantiers")
    devis   = relationship("Devis",  back_populates="chantier")
    factures = relationship("Facture", back_populates="chantier")