from playwright.sync_api import sync_playwright
import time


def _scrape_page(page, url, city, query, cookies_accepted):
    """
    Scrape une seule page de résultats Pages Jaunes.
    Retourne (liste d'entreprises, cookies_accepted).
    """
    companies = []

    print(f"  → Ouverture : {url}")
    page.goto(url, wait_until="domcontentloaded")
    page.wait_for_timeout(3000)

    # Accepter les cookies une seule fois
    if not cookies_accepted:
        try:
            page.click("button.button__acceptAll")
            print("  ✓ Cookies acceptés")
            page.wait_for_timeout(2000)
            cookies_accepted = True
        except:
            print("  - Pas de popup cookies")

    # Attendre les résultats
    try:
        page.wait_for_selector(".bi-with-visual", timeout=15000)
    except:
        print("  ✗ Aucun résultat trouvé sur cette page")
        return companies, cookies_accepted

    results = page.query_selector_all("a.bi-denomination")
    print(f"  ✓ {len(results)} entreprises trouvées")

    for element in results:
        try:
            name_el = element.query_selector("h3")
            if not name_el:
                continue

            name = name_el.inner_text().strip()
            link = element.get_attribute("href")

            if link and link != "#":
                link = "https://www.pagesjaunes.fr" + link
            else:
                link = None

            companies.append({
                "name": name,
                "url": link,
                "email": None,
                "industry": query.lower(),
                "city": city
            })
        except Exception as e:
            print(f"  ⚠ Erreur élément : {e}")
            continue

    return companies, cookies_accepted


def _has_next_page(page, current_count, page_num):
    """
    Détermine s'il faut continuer la pagination.

    Stratégie robuste en 3 niveaux (du plus fiable au moins fiable) :
      1. Si la page courante a renvoyé < 20 résultats → dernière page
      2. Chercher un lien <a> dont le href contient ?page=<page_num+1>
      3. Chercher des sélecteurs CSS connus pour le bouton "suivant"
    """

    # Niveau 1 : moins de 20 résultats = dernière page
    if current_count < 20:
        return False

    # Niveau 2 : chercher un lien avec la prochaine page dans l'URL
    try:
        next_page_num = page_num + 1
        next_link = page.query_selector(
            f'a[href*="page={next_page_num}"]'
        )
        if next_link:
            return True
    except:
        pass

    # Niveau 3 : sélecteurs CSS connus (peut changer côté Pages Jaunes)
    selectors = [
        "a.pagination-next:not(.disabled)",
        "a[aria-label*='suivant']",
        "a[aria-label*='next']",
        "li.next:not(.disabled) a",
        ".pagination .next:not(.disabled)",
    ]
    for selector in selectors:
        try:
            el = page.query_selector(selector)
            if el:
                return True
        except:
            continue

    return False


def scrape_pagesjaunes(
    query="nettoyage",
    locations=None,
    max_pages=3,
    headless=True
):
    """
    Scrape Pages Jaunes pour plusieurs villes et plusieurs pages.

    Args:
        query      : Terme de recherche (ex: "nettoyage", "syndic")
        locations  : Liste de villes (ex: ["paris", "lyon", "marseille"])
                     Par défaut : ["paris"]
        max_pages  : Nombre max de pages par ville (défaut : 3)
        headless   : True = navigateur invisible (défaut : True)

    Returns:
        Liste de dicts {name, url, email, industry, city}
    """

    if locations is None:
        locations = ["paris"]

    all_companies = []
    seen_names = set()  # Éviter les doublons inter-villes

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()

        # User-agent pour éviter la détection bot
        page.set_extra_http_headers({
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        })

        cookies_accepted = False

        for city in locations:

            print(f"\n{'='*40}")
            print(f"📍 Ville : {city.upper()}")
            print(f"{'='*40}")

            city_count = 0

            for page_num in range(1, max_pages + 1):

                # Construction de l'URL avec pagination
                if page_num == 1:
                    url = f"https://www.pagesjaunes.fr/recherche/{city}/{query}"
                else:
                    url = f"https://www.pagesjaunes.fr/recherche/{city}/{query}?page={page_num}"

                print(f"\n  📄 Page {page_num}/{max_pages}")

                companies, cookies_accepted = _scrape_page(
                    page, url, city, query, cookies_accepted
                )

                # Dédoublonnage
                new_companies = []
                for c in companies:
                    key = c["name"].lower().strip()
                    if key not in seen_names:
                        seen_names.add(key)
                        new_companies.append(c)
                    else:
                        print(f"  ↩ Doublon ignoré : {c['name']}")

                all_companies.extend(new_companies)
                city_count += len(new_companies)

                # Vérifier s'il faut continuer la pagination
                if not _has_next_page(page, len(companies), page_num):
                    print(f"  ⏹ Dernière page atteinte pour {city}")
                    break

                # Délai anti-bot entre les pages
                time.sleep(2)

            print(f"\n  ✅ {city_count} prospects récupérés pour {city}")

        browser.close()

    print(f"\n{'='*40}")
    print(f"🎯 TOTAL : {len(all_companies)} prospects sur {len(locations)} ville(s)")
    print(f"{'='*40}\n")

    return all_companies