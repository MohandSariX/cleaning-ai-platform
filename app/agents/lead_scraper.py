from app.core.database import SessionLocal
from app.models.prospect import Prospect
from app.agents.company_details_scraper import scrape_company_details
from app.agents.scraper_pagesjaunes import scrape_pagesjaunes
from app.agents.email_finder import find_email_from_website
from urllib.parse import urlparse


def _get_domain(url):
    """Extrait le domaine depuis une URL."""
    if not url:
        return None
    try:
        if not url.startswith("http"):
            url = "https://" + url
        return urlparse(url).netloc.lower().replace("www.", "")
    except:
        return None


def run_lead_scraper(query="nettoyage", locations=None, max_pages=3):
    """
    Lance le pipeline de scraping complet.

    Args:
        query     : Terme recherché sur Pages Jaunes (ex: "nettoyage")
        locations : Liste de villes (ex: ["paris", "lyon", "marseille"])
        max_pages : Nombre max de pages Pages Jaunes par ville
    """

    if locations is None:
        locations = ["paris"]

    db = SessionLocal()

    # Étape 1 : Scraper Pages Jaunes (multi-villes + multi-pages)
    companies = scrape_pagesjaunes(
        query=query,
        locations=locations,
        max_pages=max_pages
    )

    new_count = 0
    skip_count = 0
    email_count = 0

    # Cache des domaines déjà rencontrés dans ce run
    # (évite de scraper le même site pour 4 franchises GSF par ex.)
    seen_domains_this_run = {}  # domain -> email déjà trouvé

    for company in companies:

        # Ignorer les entreprises déjà en base
        existing = db.query(Prospect).filter(
            Prospect.company_name == company["name"]
        ).first()

        if existing:
            skip_count += 1
            print(f"  ↩ Déjà en base : {company['name']}")
            continue

        # Ignorer les fiches sans URL valide
        if not company.get("url"):
            skip_count += 1
            continue

        # Étape 2 : Scraper la fiche entreprise
        details = scrape_company_details(company["url"])

        if not details:
            skip_count += 1
            continue

        # Étape 3 : Chercher l'email sur le site web
        email = None
        website = details.get("website")
        domain = _get_domain(website)

        if website:
            if domain and domain in seen_domains_this_run:
                # Réutiliser l'email déjà trouvé pour ce domaine
                email = seen_domains_this_run[domain]
                if email:
                    print(f"  ♻ Email réutilisé depuis {domain} : {email}")
            else:
                email = find_email_from_website(website)
                if domain:
                    seen_domains_this_run[domain] = email  # même si None
                if email:
                    email_count += 1

        # Étape 4 : Sauvegarder en base
        prospect = Prospect(
            company_name=company["name"],
            industry=company.get("industry", "nettoyage"),
            city=company.get("city"),
            phone=details.get("phone"),
            address=details.get("address"),
            email=email,
            status="new"
        )

        db.add(prospect)
        new_count += 1
        email_indicator = f"📧 {email}" if email else "❌ pas d'email"
        print(f"  ✅ Ajouté : {company['name']} ({company.get('city', '?')}) — {email_indicator}")

    db.commit()
    db.close()

    print(f"\n{'='*40}")
    print(f"📊 RÉSUMÉ PIPELINE")
    print(f"  Trouvés     : {len(companies)}")
    print(f"  Ajoutés     : {new_count}")
    print(f"  Ignorés     : {skip_count}")
    print(f"  Avec email  : {email_count}")
    print(f"{'='*40}\n")