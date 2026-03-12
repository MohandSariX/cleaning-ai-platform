from app.agents.lead_scraper import run_lead_scraper
from app.agents.lead_scorer import run_lead_scoring
from app.agents.email_outreach import run_email_outreach

# ============================================================
#  ⚙️  CONFIGURATION CENTRALE — modifie ici
# ============================================================

QUERY = "nettoyage"

LOCATIONS = [
    "Saint-Maur-des-Fossés",
]

MAX_PAGES = 1   # ~20 résultats/page → 3 pages × 11 villes = ~660 prospects max

# ============================================================


def run_pipeline():

    print(f"\n🚀 Lancement pipeline")
    print(f"   Recherche   : '{QUERY}'")
    print(f"   Villes      : {', '.join(LOCATIONS)}")
    print(f"   Pages/ville : {MAX_PAGES}")
    print(f"   Prospects max : ~{MAX_PAGES * len(LOCATIONS) * 20}\n")

    print("----- SCRAPER -----")
    run_lead_scraper(query=QUERY, locations=LOCATIONS, max_pages=MAX_PAGES)

    print("----- SCORING -----")
    run_lead_scoring()

    print("----- OUTREACH -----")
    run_email_outreach()

    print("----- FIN PIPELINE -----")


if __name__ == "__main__":
    run_pipeline()