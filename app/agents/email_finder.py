import requests
import re
import urllib3
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

EMAIL_REGEX = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]+"

# Réseaux sociaux et agrégateurs à ignorer entièrement
BLOCKED_DOMAINS = {
    "facebook.com", "instagram.com", "twitter.com", "x.com",
    "linkedin.com", "youtube.com", "tiktok.com", "pinterest.com",
    "google.com", "maps.google.com", "pagesjaunes.fr",
    "site-solocal.com", "site-privilege.pagesjaunes.fr",
}

# Préfixes d'emails à rejeter (faux positifs fréquents)
BLOCKED_EMAIL_PREFIXES = {
    "noreply", "no-reply", "donotreply", "do-not-reply",
    "webmaster", "postmaster", "mailer-daemon",
    "support", "info@example", "test@", "exemple@",
    "admin@example", "user@example",
}

# Extensions de fichiers souvent captées par le regex
BLOCKED_EMAIL_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp",
    ".woff", ".woff2", ".ttf", ".eot", ".otf",
    ".css", ".js", ".min",
}


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
    """Retourne True si l'URL appartient à un domaine blacklisté."""
    try:
        domain = urlparse(url).netloc.lower().replace("www.", "")
        return any(blocked in domain for blocked in BLOCKED_DOMAINS)
    except:
        return False


def is_valid_email(email):
    """Filtre les faux positifs : extensions de fichiers, noreply, etc."""

    email_lower = email.lower()

    # Rejeter si l'email contient une extension de fichier
    if any(ext in email_lower for ext in BLOCKED_EMAIL_EXTENSIONS):
        return False

    # Rejeter les adresses noreply / webmaster / etc.
    local_part = email_lower.split("@")[0]
    if any(local_part.startswith(prefix) for prefix in BLOCKED_EMAIL_PREFIXES):
        return False

    # Rejeter les adresses trop courtes ou sans domaine valide
    parts = email.split("@")
    if len(parts) != 2:
        return False
    domain_part = parts[1]
    if "." not in domain_part or len(domain_part) < 4:
        return False

    return True


def extract_best_email(text):
    """
    Extrait le meilleur email depuis un texte HTML.
    Préfère les emails de contact génériques (contact@, hello@, info@)
    sur les emails personnels.
    """
    emails = re.findall(EMAIL_REGEX, text)
    valid_emails = [e for e in emails if is_valid_email(e)]

    if not valid_emails:
        return None

    # Priorité : contact@, hello@, bonjour@, info@
    priority_prefixes = ["contact", "hello", "bonjour", "info", "accueil", "devis"]
    for email in valid_emails:
        local = email.lower().split("@")[0]
        if any(local.startswith(p) for p in priority_prefixes):
            return email

    # Sinon retourner le premier email valide
    return valid_emails[0]


def find_email_from_website(url):

    try:
        url = normalize_url(url)

        if not url:
            return None

        # Ignorer les réseaux sociaux et agrégateurs
        if is_blocked_domain(url):
            print(f"  ⏭ Domaine ignoré : {url}")
            return None

        print(f"Opening website: {url}")

        response = requests.get(
            url,
            timeout=10,
            verify=False,
            headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
        )

        html = response.text

        # 1️⃣ Chercher email sur la homepage
        email = extract_best_email(html)
        if email:
            return email

        # 2️⃣ Chercher les pages contact / mentions légales
        soup = BeautifulSoup(html, "html.parser")
        links = []

        for a in soup.find_all("a", href=True):
            href = a["href"]
            keywords = [
                "contact", "contactez", "nous-contacter",
                "mentions", "legal", "legales",
                "about", "a-propos", "qui-sommes",
            ]
            if any(k in href.lower() for k in keywords):
                full_link = urljoin(url, href)
                # Rester sur le même domaine
                if urlparse(full_link).netloc == urlparse(url).netloc:
                    links.append(full_link)

        links = list(dict.fromkeys(links))[:5]  # dédoublonner, max 5

        # 3️⃣ Scraper les pages internes
        for link in links:
            try:
                print(f"Checking page: {link}")
                r = requests.get(
                    link,
                    timeout=10,
                    verify=False,
                    headers={"User-Agent": "Mozilla/5.0"}
                )
                email = extract_best_email(r.text)
                if email:
                    return email
            except:
                continue

    except Exception as e:
        print(f"  ⚠ Email scraping error: {e}")

    return None