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
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await self.search_google_maps(page)
            await browser.close()

    async def search_google_maps(self, page):
        search_query = f"{self.category} in {self.city}"
        logging.info(f"Searching for: {search_query}")

        await page.goto('https://www.google.com/maps')
        await page.fill('input[aria-label="Search Google Maps"]', search_query)
        await page.keyboard.press('Enter')
        await page.wait_for_load_state('networkidle')

        await self.extract_data(page)

    async def extract_data(self, page):
        logging.info("Extracting data...")
        businesses = await page.query_selector_all('div[role="article"]')

        with open(self.output_file, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['Name', 'Phone', 'Website'])

            for business in businesses:
                name = await business.query_selector_eval('h3', 'el => el.textContent') or 'N/A'
                phone = await business.query_selector_eval('span[aria-label*="Phone"]', 'el => el.textContent') or 'N/A'
                website = await business.query_selector_eval('a[aria-label*="Website"]', 'el => el.href') or 'N/A'
                
                logging.info(f"Found business: {name}, Phone: {phone}, Website: {website}")
                writer.writerow([name, phone, website])

if __name__ == '__main__':
    category = 'Restaurants'
    city = 'San Francisco'
    scraper = GoogleMapsScraper(category, city)
    asyncio.run(scraper.run())