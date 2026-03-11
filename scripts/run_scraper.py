import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.agents.lead_scraper import run_lead_scraper

run_lead_scraper()