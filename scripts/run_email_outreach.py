from app.core.database import SessionLocal
from app.models.prospect import Prospect
from app.agents.email_agent import send_email

db = SessionLocal()

prospects = db.query(Prospect).filter(Prospect.lead_score > 70)

for prospect in prospects:

    send_email(prospect.email, prospect.company_name)

    print("email envoyé à", prospect.company_name)