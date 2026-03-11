from app.agents.lead_scraper import run_lead_scraper
from app.agents.lead_scorer import run_lead_scoring
from app.agents.email_outreach import run_email_outreach


def run_pipeline():

    print("----- SCRAPER -----")
    run_lead_scraper()

    print("----- SCORING -----")
    run_lead_scoring()

    print("----- OUTREACH -----")
    run_email_outreach()

    print("----- FIN PIPELINE -----")


if __name__ == "__main__":
    run_pipeline()