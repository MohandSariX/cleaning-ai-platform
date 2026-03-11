from app.core.database import SessionLocal
from app.models.prospect import Prospect
from app.agents.company_details_scraper import scrape_company_details
from app.agents.scraper_pagesjaunes import scrape_pagesjaunes
from app.agents.email_finder import find_email_from_website


def run_lead_scraper():

    db = SessionLocal()

    companies = scrape_pagesjaunes()

    for company in companies:

        existing = db.query(Prospect).filter(
            Prospect.company_name == company["name"]
        ).first()

        if existing:
            continue

        details = scrape_company_details(company["url"])

        if not details:
            continue

        email = None

        if details["website"]:
            email = find_email_from_website(details["website"])

        prospect = Prospect(
            company_name=company["name"],
            industry=company["industry"],
            phone=details.get("phone"),
            address=details.get("address"),
            email=email,
            status="new"
        )

        db.add(prospect)

    db.commit()

    db.close()

    print(f"{len(companies)} prospects scraped")