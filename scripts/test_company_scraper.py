import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.company_details_scraper import scrape_company_details

url = "https://www.pagesjaunes.fr/pros/02454825"

data = scrape_company_details(url)

print(data)