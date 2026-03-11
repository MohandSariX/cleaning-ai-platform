from sqlalchemy.orm import Session
from app.models.prospect import Prospect
from app.core.database import SessionLocal


def calculate_score(prospect):

    industry_scores = {
        "accounting": 80,
        "real_estate": 70,
        "office": 90,
        "restaurant": 20
    }

    return industry_scores.get(prospect.industry, 50)


def run_lead_scoring():

    db: Session = SessionLocal()

    prospects = db.query(Prospect).all()

    for prospect in prospects:

        score = calculate_score(prospect)

        prospect.lead_score = score

    db.commit()
    db.close()

    print("Lead scoring terminé")