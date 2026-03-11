import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Importer la config depuis run_pipeline — une seule source de vérité
from run_pipeline import QUERY, LOCATIONS, MAX_PAGES
from app.agents.lead_scraper import run_lead_scraper

if __name__ == "__main__":
    print(f"\n🚀 Lancement scraper uniquement")
    print(f"   Recherche   : '{QUERY}'")
    print(f"   Villes      : {', '.join(LOCATIONS)}")
    print(f"   Pages/ville : {MAX_PAGES}")
    print(f"   Prospects max : ~{MAX_PAGES * len(LOCATIONS) * 20}\n")

    run_lead_scraper(query=QUERY, locations=LOCATIONS, max_pages=MAX_PAGES)