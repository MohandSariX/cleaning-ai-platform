import httpx
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.prospect import Prospect


def scrape_mock_companies():

    # Pour commencer on simule des entreprises
    return [
        {
            "company_name": "Cabinet Comptable Paris",
            "industry": "accounting",
            "email": "contact@cabinet-paris.fr",
            "phone": "0102030405",
            "address": "Paris"
        },
        {
            "company_name": "Agence Immo Lyon",
            "industry": "real_estate",
            "email": "contact@immo-lyon.fr",
            "phone": "0601020304",
            "address": "Lyon"
        }
    ]


def save_prospects(companies):

    db: Session = SessionLocal()

    for company in companies:

        prospect = Prospect(
            company_name=company["company_name"],
            industry=company["industry"],
            email=company["email"],
            phone=company["phone"],
            address=company["address"],
            lead_score=0.5
        )

        db.add(prospect)

    db.commit()
    db.close()


def run_lead_scraper():

    companies = scrape_mock_companies()

    save_prospects(companies)

    print("Prospects added.")