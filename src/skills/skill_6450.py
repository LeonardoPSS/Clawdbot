import asyncio
import csv
import logging
from playwright.async_api import async_playwright

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class GoogleMapsScraper:
    def __init__(self, category, city, output_file='output.csv'):
        self.category = category
        self.city = city
        self.output_file = output_file

    async def run(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            await self.search_google_maps(page)
            await self.extract_data(page)
            await browser.close()

    async def search_google_maps(self, page):
        search_url = f"https://www.google.com/maps/search/{self.category}+in+{self.city}"
        logging.info(f"Navigating to {search_url}")
        await page.goto(search_url)

    async def extract_data(self, page):
        logging.info("Extracting data...")
        await page.wait_for_selector("div[role='article']")

        businesses = await page.query_selector_all("div[role='article']")
        data = []

        for business in businesses:
            name = await business.query_selector("h3 span")
            name_text = await name.inner_text() if name else "N/A"

            phone = await business.query_selector("span[aria-label*='Phone']")
            phone_text = await phone.inner_text() if phone else "N/A"

            website = await business.query_selector("a[aria-label*='Website']")
            website_href = await website.get_attribute('href') if website else "N/A"

            logging.info(f"Extracted: {name_text}, {phone_text}, {website_href}")
            data.append([name_text, phone_text, website_href])

        self.save_to_csv(data)

    def save_to_csv(self, data):
        logging.info(f"Saving data to {self.output_file}")
        with open(self.output_file, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['Name', 'Phone', 'Website'])
            writer.writerows(data)
        logging.info("Data saved successfully.")

if __name__ == "__main__":
    category = "restaurants"
    city = "New York"
    scraper = GoogleMapsScraper(category, city)
    asyncio.run(scraper.run())