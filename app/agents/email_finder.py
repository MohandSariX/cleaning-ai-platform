"""
Agent Email Finder — Trouve les emails des entreprises.
Basé sur le scraper BeautifulSoup existant + pipeline Pappers + déduction SMTP.
"""

import re
import os
import socket
import requests
import urllib3
import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from app.core.database import SessionLocal
from app.models.prospect import Prospect
from app.agents.activity_logger import log_system, log_error

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logger = logging.getLogger("proprexis.email_finder")

EMAIL_REGEX = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]+"

BLOCKED_DOMAINS = {
    "facebook.com", "instagram.com", "twitter.com", "x.com",
    "linkedin.com", "youtube.com", "tiktok.com", "pinterest.com",
    "google.com", "maps.google.com", "pagesjaunes.fr",
    "site-solocal.com", "site-privilege.pagesjaunes.fr",
}

BLOCKED_EMAIL_PREFIXES = {
    "noreply", "no-reply", "donotreply", "do-not-reply",
    "webmaster", "postmaster", "mailer-daemon",
    "support", "info@example", "test@", "exemple@",
    "admin@example", "user@example",
}

BLOCKED_EMAIL_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp",
    ".woff", ".woff2", ".ttf", ".eot", ".otf",
    ".css", ".js", ".min",
}

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}


def normalize_url(url):
    if not url:
        return None
    url = url.strip()
    if url.startswith("www"):
        url = "https://" + url
    if not url.startswith("http"):
        url = "https://" + url
    return url


def is_blocked_domain(url):
    try:
        domain = urlparse(url).netloc.lower().replace("www.", "")
        return any(blocked in domain for blocked in BLOCKED_DOMAINS)
    except Exception:
        return False


def is_valid_email(email):
    email_lower = email.lower()
    if any(ext in email_lower for ext in BLOCKED_EMAIL_EXTENSIONS):
        return False
    local_part = email_lower.split("@")[0]
    if any(local_part.startswith(prefix) for prefix in BLOCKED_EMAIL_PREFIXES):
        return False
    parts = email.split("@")
    if len(parts) != 2:
        return False
    domain_part = parts[1]
    if "." not in domain_part or len(domain_part) < 4:
        return False
    return True


def extract_best_email(text):
    emails = re.findall(EMAIL_REGEX, text)
    valid_emails = [e for e in emails if is_valid_email(e)]
    if not valid_emails:
        return None
    priority_prefixes = ["contact", "hello", "bonjour", "info", "accueil", "devis"]
    for email in valid_emails:
        local = email.lower().split("@")[0]
        if any(local.startswith(p) for p in priority_prefixes):
            return email
    return valid_emails[0]


def find_email_from_website(url):
    """Scrape un site web pour trouver un email de contact."""
    try:
        url = normalize_url(url)
        if not url or is_blocked_domain(url):
            return None

        logger.debug(f"Scraping : {url}")
        response = requests.get(url, timeout=10, verify=False, headers=HEADERS)
        html = response.text

        # 1. Chercher sur la homepage
        email = extract_best_email(html)
        if email:
            return email

        # 2. Chercher les pages contact / mentions légales
        soup = BeautifulSoup(html, "html.parser")
        links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            keywords = ["contact", "contactez", "nous-contacter", "mentions", "legal", "legales", "about", "a-propos"]
            if any(k in href.lower() for k in keywords):
                full_link = urljoin(url, href)
                if urlparse(full_link).netloc == urlparse(url).netloc:
                    links.append(full_link)

        links = list(dict.fromkeys(links))[:5]

        for link in links:
            try:
                r = requests.get(link, timeout=10, verify=False, headers=HEADERS)
                email = extract_best_email(r.text)
                if email:
                    return email
            except Exception:
                continue

    except Exception as e:
        logger.debug(f"Scraping erreur : {e}")

    return None


def get_website_from_pappers(company_name: str, city: str = None, siren: str = None) -> tuple:
    """Récupère site web + dirigeant depuis Pappers. Retourne (website, prenom, nom)"""
    api_key = os.getenv("PAPPERS_API_KEY")
    if not api_key:
        return None, None, None
    try:
        if siren:
            res = requests.get(
                "https://api.pappers.fr/v2/entreprise",
                params={"api_token": api_key, "siren": siren},
                timeout=10
            )
            data = res.json()
        else:
            res = requests.get(
                "https://api.pappers.fr/v2/recherche",
                params={"api_token": api_key, "q": company_name, "ville": city or "", "par_page": 1},
                timeout=10
            )
            resultats = res.json().get("resultats", [])
            if not resultats:
                return None, None, None
            siren = resultats[0].get("siren")
            res = requests.get(
                "https://api.pappers.fr/v2/entreprise",
                params={"api_token": api_key, "siren": siren},
                timeout=10
            )
            data = res.json()

        website = data.get("site_web") or data.get("siege", {}).get("site_web")
        prenom, nom = None, None
        dirigeants = data.get("dirigeants", [])
        if dirigeants:
            d = dirigeants[0]
            prenom = d.get("prenom", "")
            nom = d.get("nom", "")

        return website, prenom, nom

    except Exception as e:
        logger.debug(f"Pappers website erreur : {e}")
        return None, None, None


def generate_email_candidates(prenom: str, nom: str, domain: str) -> list:
    """Génère les formats d'email les plus courants."""
    if not domain:
        return []
    p = (prenom or "").lower().strip()
    n = (nom or "").lower().strip()
    for old, new in [("é","e"),("è","e"),("ê","e"),("à","a"),("â","a"),("ô","o"),("ù","u"),("ç","c"),("-",""),(" ","")]:
        p = p.replace(old, new)
        n = n.replace(old, new)

    candidates = []
    if p and n:
        candidates = [
            f"{p}.{n}@{domain}", f"{p[0]}.{n}@{domain}",
            f"{p}{n}@{domain}", f"{p}@{domain}",
        ]
    return candidates + [f"contact@{domain}", f"info@{domain}", f"direction@{domain}"]


def verify_email_simple(email: str) -> bool:
    """Vérifie que le domaine de l'email est accessible."""
    try:
        domain = email.split("@")[1]
        socket.setdefaulttimeout(3)
        socket.gethostbyname(domain)
        return True
    except Exception:
        return False


def find_email_for_prospect(prospect_id: int) -> dict:
    """Pipeline complet pour trouver l'email d'un prospect."""
    db = SessionLocal()
    try:
        prospect = db.query(Prospect).filter(Prospect.id == prospect_id).first()
        if not prospect:
            return {"status": "error", "message": "Prospect introuvable"}
        if prospect.email:
            return {"status": "already_has_email", "email": prospect.email}

        # Extraire SIREN si disponible
        siren = None
        if prospect.score_explanation:
            match = re.search(r'SIREN\s*:\s*(\d{9})', prospect.score_explanation)
            if match:
                siren = match.group(1)

        # Étape 1 — Site web via Pappers
        website, prenom, nom = get_website_from_pappers(prospect.company_name, prospect.city, siren)

        # Étape 2 — Scraper le site
        email_found = None
        if website:
            email_found = find_email_from_website(website)

        # Étape 3 — Déduction + vérification domaine
        if not email_found and website:
            try:
                domain = urlparse(normalize_url(website)).netloc.replace("www.", "")
            except Exception:
                domain = None
            if domain:
                for candidate in generate_email_candidates(prenom, nom, domain)[:6]:
                    if verify_email_simple(candidate):
                        email_found = candidate
                        break

        # Étape 4 — Sauvegarder
        if email_found:
            prospect.email = email_found
            if prenom and nom and prospect.score_explanation and "Dirigeant" not in prospect.score_explanation:
                prospect.score_explanation += f"\nDirigeant : {prenom} {nom}"
            db.commit()
            logger.info(f"✅ Email trouvé pour {prospect.company_name} : {email_found}")
            return {"status": "found", "email": email_found}

        return {"status": "not_found", "company": prospect.company_name}

    except Exception as e:
        logger.error(f"Erreur email finder {prospect_id} : {e}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


def find_emails_batch(limit: int = 20) -> dict:
    """Cherche les emails pour les N prochains prospects sans email."""
    db = SessionLocal()
    try:
        prospects = db.query(Prospect).filter(
            Prospect.email == None,
            Prospect.lead_score >= 50,
            Prospect.status.in_(["scored", "email_generated", "contacted"])
        ).order_by(Prospect.lead_score.desc()).limit(limit).all()

        if not prospects:
            return {"status": "empty", "found": 0}

        found = 0
        not_found = 0
        for prospect in prospects:
            result = find_email_for_prospect(prospect.id)
            if result["status"] == "found":
                found += 1
            else:
                not_found += 1

        if found > 0:
            log_system(f"📧 Email finder batch : {found} emails trouvés", status="success")

        return {"status": "done", "found": found, "not_found": not_found}
    finally:
        db.close()