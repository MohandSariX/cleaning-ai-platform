import requests
import re
import urllib3
from bs4 import BeautifulSoup
from urllib.parse import urljoin

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

EMAIL_REGEX = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]+"


def normalize_url(url):

    if not url:
        return None

    if url.startswith("www"):
        url = "https://" + url

    if not url.startswith("http"):
        url = "https://" + url

    return url


def extract_email(text):

    emails = re.findall(EMAIL_REGEX, text)

    for email in emails:

        if any(x in email for x in [".png", ".jpg", ".jpeg", ".svg"]):
            continue

        return email

    return None


def find_email_from_website(url):

    try:

        url = normalize_url(url)

        if not url:
            return None

        if "facebook" in url or "instagram" in url:
            return None

        print(f"Opening website: {url}")

        response = requests.get(
            url,
            timeout=10,
            verify=False,
            headers={"User-Agent": "Mozilla/5.0"}
        )

        html = response.text

        # 1️⃣ chercher email sur homepage
        email = extract_email(html)

        if email:
            return email

        # 2️⃣ chercher liens internes
        soup = BeautifulSoup(html, "html.parser")

        links = []

        for a in soup.find_all("a", href=True):

            href = a["href"]

            keywords = [
                "contact",
                "contactez",
                "mentions",
                "legal",
                "about",
                "a-propos"
            ]

            if any(k in href.lower() for k in keywords):

                full_link = urljoin(url, href)
                links.append(full_link)

        # limiter à 5 pages
        links = list(set(links))[:5]

        # 3️⃣ scraper pages contact
        for link in links:

            try:

                print(f"Checking page: {link}")

                r = requests.get(
                    link,
                    timeout=10,
                    verify=False,
                    headers={"User-Agent": "Mozilla/5.0"}
                )

                email = extract_email(r.text)

                if email:
                    return email

            except:
                continue

    except Exception as e:
        print("Email scraping error:", e)

    return None