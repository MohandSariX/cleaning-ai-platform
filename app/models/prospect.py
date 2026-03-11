from sqlalchemy import Column, Integer, String, Float
from app.core.database import Base

class Prospect(Base):

    __tablename__ = "prospects"

    id = Column(Integer, primary_key=True, index=True)

    company_name = Column(String)
    industry = Column(String)

    email = Column(String)
    phone = Column(String)
    city = Column(String)

    address = Column(String)

    lead_score = Column(Float, default=0)

    status = Column(String, default="new")
    