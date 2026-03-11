from playwright.sync_api import sync_playwright


def scrape_company_details(url):

    data = {
        "phone": None,
        "address": None,
        "website": None
    }

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_extra_http_headers({
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        })

        print(f"Opening: {url}")

        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        # ── Téléphone ──────────────────────────────────────────────
        # Pages Jaunes change régulièrement ses sélecteurs CSS.
        # On essaie plusieurs en cascade, du plus précis au plus large.
        phone_selectors = [
            "span.coord-numero",            # ancien sélecteur
            "a[href^='tel:']",              # lien tel: universel
            "[class*='numero']",            # classe contenant "numero"
            "[class*='phone']",             # classe contenant "phone"
            "[class*='coord'] span",        # span dans un bloc coord
        ]

        for selector in phone_selectors:
            try:
                el = page.query_selector(selector)
                if el:
                    text = el.inner_text().strip()
                    # Vérifier que ça ressemble à un numéro
                    digits = text.replace(" ", "").replace(".", "")
                    if len(digits) >= 8 and any(c.isdigit() for c in digits):
                        data["phone"] = text
                        break
                    # Pour les liens tel:
                    href = el.get_attribute("href") or ""
                    if href.startswith("tel:"):
                        data["phone"] = href.replace("tel:", "").strip()
                        break
            except:
                continue

        if not data["phone"]:
            print("  ⚠ Téléphone non trouvé")

        # ── Adresse ────────────────────────────────────────────────
        address_selectors = [
            ".address-container span.noTrad",
            ".address-container span",
            "[class*='address'] span",
            "[class*='adresse'] span",
        ]

        for selector in address_selectors:
            try:
                el = page.query_selector(selector)
                if el:
                    text = el.inner_text().strip()
                    if len(text) > 5:
                        data["address"] = text
                        break
            except:
                continue

        # ── Site web ────────────────────────────────────────────────
        website_selectors = [
            ".lvs-container span.value",
            "a[class*='site-web']",
            "a[href*='http'][data-pjlb-event*='site']",
            "[class*='website'] span",
            "[class*='web'] span.value",
        ]

        for selector in website_selectors:
            try:
                el = page.query_selector(selector)
                if el:
                    # D'abord essayer le texte (souvent l'URL affichée)
                    text = el.inner_text().strip()
                    if text and "." in text and len(text) > 4:
                        data["website"] = text
                        break
                    # Sinon l'attribut href
                    href = el.get_attribute("href") or ""
                    if href.startswith("http"):
                        data["website"] = href
                        break
            except:
                continue

        print(f"Extracted: {data}")
        browser.close()

    return data