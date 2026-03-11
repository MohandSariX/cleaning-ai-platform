from playwright.sync_api import sync_playwright


def scrape_company_details(url):

    data = {
        "phone": None,
        "address": None,
        "website": None
    }

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        print("Opening:", url)

        page.goto(url)

        # attendre que le téléphone apparaisse
        try:
            page.wait_for_selector("span.coord-numero", timeout=10000)
        except:
            print("Phone element not found")

        # téléphone
        phone = page.query_selector("span.coord-numero")
        if phone:
            data["phone"] = phone.inner_text().strip()

        # adresse
        address = page.query_selector(".address-container span.noTrad")
        if address:
            data["address"] = address.inner_text().strip()

        # site web
        website = page.query_selector(".lvs-container span.value")
        if website:
            data["website"] = website.inner_text().strip()

        print("Extracted:", data)

        browser.close()

    return data