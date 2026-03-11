from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.prospect import Prospect


def run_email_outreach():

    db: Session = SessionLocal()

    prospects = db.query(Prospect).filter(
        Prospect.lead_score >= 70,
        Prospect.status == "new"
    ).all()

    for prospect in prospects:

        print("Email à envoyer à :", prospect.company_name)
        print("Email :", prospect.email)
        print("Score :", prospect.lead_score)
        print("-----")
        prospect.status = "contacted"

    db.commit()
    db.close()