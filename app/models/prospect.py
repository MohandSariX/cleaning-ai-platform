from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class Prospect(Base):

    __tablename__ = "prospects"

    id = Column(Integer, primary_key=True, index=True)

    # Infos entreprise
    company_name = Column(String)
    industry     = Column(String)
    city         = Column(String)
    address      = Column(String)
    website      = Column(String)

    # Contact
    email = Column(String)
    phone = Column(String)

    # Scoring
    lead_score        = Column(Float, default=0)
    score_label       = Column(String)
    score_explanation = Column(Text)

    # Statut pipeline
    # new | scored | email_generated | contacted | replied | signed | lost
    status = Column(String, default="new")

    # Timestamps
    created_at     = Column(DateTime, server_default=func.now())
    updated_at     = Column(DateTime, onupdate=func.now())
    last_contacted = Column(DateTime, nullable=True)