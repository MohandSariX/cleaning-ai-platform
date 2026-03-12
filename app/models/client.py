from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)

    # Lien vers le prospect d'origine
    prospect_id = Column(Integer, ForeignKey("prospects.id"), nullable=True)

    # Infos entreprise
    company_name  = Column(String, nullable=False)
    contact_name  = Column(String)        # Nom du gérant / interlocuteur
    email         = Column(String)
    phone         = Column(String)
    address       = Column(String)
    city          = Column(String)
    website       = Column(String)
    siret         = Column(String)        # Numéro SIRET

    # Type de prestation principale
    # bureaux | fin_chantier | copropriete | autre
    service_type  = Column(String, default="bureaux")

    # Statut
    # actif | pause | perdu | prospect_converti
    status        = Column(String, default="actif")

    notes         = Column(Text)

    # Timestamps
    created_at    = Column(DateTime, server_default=func.now())
    updated_at    = Column(DateTime, onupdate=func.now())
    signed_at     = Column(DateTime, nullable=True)   # Date de signature du contrat

    # Relations
    devis     = relationship("Devis",    back_populates="client", cascade="all, delete-orphan")
    chantiers = relationship("Chantier", back_populates="client", cascade="all, delete-orphan")
    factures  = relationship("Facture",  back_populates="client", cascade="all, delete-orphan")