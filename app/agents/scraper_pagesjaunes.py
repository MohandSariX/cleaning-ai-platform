from playwright.sync_api import sync_playwright


from playwright.sync_api import sync_playwright


def scrape_pagesjaunes(query="Syndic", location="paris"):

    url = f"https://www.pagesjaunes.fr/recherche/{location}/{query}"

    companies = []

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        print("Opening:", url)

        page.goto(url, wait_until="domcontentloaded")

        page.wait_for_timeout(3000)

        # cookies
        try:
            page.click("button.button__acceptAll")
            print("Cookies accepted")
            page.wait_for_timeout(2000)
        except:
            print("No cookie popup")

        page.wait_for_selector(".bi-with-visual", timeout=15000)

        results = page.query_selector_all("a.bi-denomination")

        print("Found elements:", len(results))

        for element in results:

            name = element.query_selector("h3").inner_text().strip()

            link = element.get_attribute("href")

            if link:
                link = "https://www.pagesjaunes.fr" + link

            companies.append({
                "name": name,
                "url": link,
                "email": None,
                "industry": "office"
            })

        browser.close()

    return companies