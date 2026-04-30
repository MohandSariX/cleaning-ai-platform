from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy import DateTime
from app.core.database import Base


class DevisTemplate(Base):
    __tablename__ = "devis_templates"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id', ondelete='CASCADE'), nullable=True, index=True)

    # Nom du template
    name = Column(String, nullable=False)

    # Catégorie : BTP, Immobilier, Bureaux, Hotels
    category = Column(String, nullable=True, index=True)

    # Type de prestation : bureaux, fin_chantier, copropriete, vitrerie, autre
    type_prestation = Column(String, nullable=True, index=True)

    # Description du template
    description = Column(Text, nullable=True)

    # Structure du template (JSON)
    # {
    #   "sections": [
    #     {"title": "Prestation", "content": "{{description}}"},
    #     {"title": "Prix", "content": "Montant HT: {{montant_ht}}€"}
    #   ],
    #   "footer": "Conditions de paiement: {{conditions_paiement}}"
    # }
    template_json = Column(JSON, nullable=False, default={})

    # Variables requises pour ce template
    # ["superficie_m2", "frequence", "description"]
    variables_required = Column(JSON, nullable=False, default=[])

    # Template par défaut pour cette catégorie/type
    is_default = Column(Boolean, default=False)

    # Actif
    active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
