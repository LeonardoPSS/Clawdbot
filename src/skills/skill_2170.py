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
        self.base_url = "https://www.google.com/maps"

    async def scrape(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            search_query = f"{self.category} in {self.city}"
            logging.info(f"Searching for: {search_query}")
            await page.goto(self.base_url)
            await page.fill("input[aria-label='Search Google Maps']", search_query)
            await page.keyboard.press('Enter')
            await page.wait_for_selector('.section-result', timeout=10000)

            results = await page.query_selector_all('.section-result')
            data = []

            for result in results:
                name = await result.query_selector_eval('.section-result-title', 'el => el.textContent')
                phone = await result.query_selector_eval('.section-result-phone-number', 'el => el.textContent', default='N/A')
                website = await result.query_selector_eval('.section-result-action-icon', 'el => el.href', default='N/A')

                data.append({
                    'Name': name.strip(),
                    'Phone': phone.strip(),
                    'Website': website.strip()
                })

            await browser.close()
            self._write_to_csv(data)

    def _write_to_csv(self, data):
        logging.info(f"Writing data to {self.output_file}")
        with open(self.output_file, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=['Name', 'Phone', 'Website'])
            writer.writeheader()
            for row in data:
                writer.writerow(row)
        logging.info("Data successfully written to CSV")

if __name__ == "__main__":
    category = "restaurants"
    city = "New York"
    scraper = GoogleMapsScraper(category, city)
    asyncio.run(scraper.scrape())