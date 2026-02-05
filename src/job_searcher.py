import logging
import time
import random
from typing import List, Dict
from playwright.sync_api import sync_playwright, Page, BrowserContext

from src.config import Settings

logger = logging.getLogger(__name__)

class JobSearcher:
    def __init__(self, config: Settings):
        self.config = config
        self.results: List[Dict] = []
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def start_browser(self):
        """Starts the Playwright browser with a persistent context and stealth measures."""
        from playwright_stealth import Stealth
        import os
        import shutil
        
        # Use a persistent user data directory to save sessions/cookies
        profile_path = os.path.abspath("browser_profile")
        
        # CLEANUP: If there's a lock file and no browser process, try to remove it
        lock_file = os.path.join(profile_path, "SingletonLock")
        if os.path.exists(lock_file):
            logger.info("Found existing browser lock file. Attempting cleanup...")
            try:
                os.remove(lock_file)
            except Exception as e:
                logger.warning(f"Could not remove lock file: {e}. Browser might still be running.")
        
        self.playwright = sync_playwright().start()
        
        try:
            self.context = self.playwright.chromium.launch_persistent_context(
                user_data_dir=profile_path,
                headless=self.config.bot.headless,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                viewport={'width': 1280, 'height': 720}
            )
        except Exception as e:
            logger.error(f"Failed to launch browser: {e}")
            # Final attempt: kill any zombie chrome and try again
            if "Target page, context or browser has been closed" in str(e):
                logger.info("Zombie chrome suspected. Killing processes and retrying...")
                os.system("taskkill /F /IM chrome.exe /T")
                time.sleep(2)
                self.context = self.playwright.chromium.launch_persistent_context(
                    user_data_dir=profile_path,
                    headless=self.config.bot.headless,
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
                )
            else:
                raise
        
        # Open a new page and navigate to Google to avoid blank screen
        self.page = self.context.new_page()
        try:
            self.page.goto("https://www.google.com")
        except: pass
        
        self.page = self.context.pages[0] if self.context.pages else self.context.new_page()
        
        # Apply stealth to the page
        stealth = Stealth()
        stealth.apply_stealth_sync(self.page)
        
        logger.info(f"Browser started with persistent profile at: {profile_path}")


    def stop_browser(self):
        """Stops the browser."""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        logger.info("Browser stopped.")

    def search_linkedin(self, keywords: List[str] = None):
        """
        Searches for jobs on LinkedIn.
        If keywords are provided, uses them. Otherwise, picks 2 random ones from config.
        """
        self.results = [] # Clear previous results
        import urllib.parse
        
        if not keywords:
            # Pick a random set of keywords to vary results
            import random
            available = self.config.profile.keywords.include
            sample_size = min(len(available), 3)
            selected = random.sample(available, sample_size)
            keywords_query = urllib.parse.quote(" ".join(selected))
        else:
            keywords_query = urllib.parse.quote(" ".join(keywords))
            
        location_query = urllib.parse.quote(self.config.profile.locations[0] if self.config.profile.locations else "Brazil")
        
        # LinkedIn Job Search URL 
        # f_TPR=r604800: Last Week
        # f_AL=true: Easy Apply Only
        # f_E=1%2C2: Experience Levels (1: Internship, 2: Entry Level)
        url = f"https://www.linkedin.com/jobs/search?keywords={keywords_query}&location={location_query}&f_TPR=r604800&f_AL=true&f_E=1%2C2"
        
        logger.info(f"Navigating to LinkedIn Search: {url}")
        self.page.goto(url)
        time.sleep(random.uniform(3, 6)) # Random wait

        # Scroll to load more (simple simulation)
        for _ in range(3):
            self.page.evaluate("window.scrollBy(0, 500)")
            time.sleep(random.uniform(1, 2))

        # Extract Job Cards
        # We try multiple selectors to handle both Guest and Logged-in states
        
        # Selectors for Guest Mode
        guest_selectors = {
            "container": "ul.jobs-search__results-list li",
            "title": "h3.base-search-card__title",
            "company": "h4.base-search-card__subtitle",
            "location": "span.job-search-card__location",
            "link": "a.base-card__full-link"
        }

        # Selectors for Logged-in Mode
        auth_selectors = {
            "container": "li.jobs-search-results-list__item, .scaffold-layout__list-container li, div.job-card-container",
            "title": "a.job-card-list__title, span.job-card-list__title, .artdeco-entity-lockup__title a, h3",
            "company": ".job-card-container__primary-description, .artdeco-entity-lockup__subtitle, .job-card-container__company-name",
            "location": ".job-card-container__metadata-item--list, .job-card-container__metadata-item, .artdeco-entity-lockup__caption",
            "link": "a.job-card-list__title, a.job-card-container__link"
        }

        # Determine which selectors to use
        is_logged_in = self.page.locator(".global-nav, .jobs-search-results-list").is_visible()
        sel = auth_selectors if is_logged_in else guest_selectors
        
        logger.info(f"Using {'Authenticated' if is_logged_in else 'Guest'} selectors.")

        # Wait for the container to appear
        try:
            self.page.wait_for_selector(sel["container"], timeout=15000)
            # Give a little extra time for the cards themselves to render
            time.sleep(2)
        except:
            logger.warning(f"Timeout waiting for primary container {sel['container']}. Trying fallbacks.")
            # Fallback for logged-in: sometimes the list is just a div with job cards
            if is_logged_in:
                try:
                    self.page.wait_for_selector("div.job-card-container", timeout=5000)
                    sel["container"] = "div.job-card-container"
                except:
                    pass
        
        job_cards = self.page.locator(sel["container"])
        count = job_cards.count()
        
        # Final fallback check
        if count == 0:
            logger.warning("No cards found with primary selectors. Trying ultra-generic.")
            job_cards = self.page.locator("li[data-occludable-job-id], div[data-job-id]")
            count = job_cards.count()

        logger.info(f"Found {count} job cards.")

        for i in range(min(count, 15)): 
            try:
                card = job_cards.nth(i)
                card.scroll_into_view_if_needed()
                
                title_elem = card.locator(sel["title"]).first
                company_elem = card.locator(sel["company"]).first
                location_elem = card.locator(sel["location"]).first
                
                title = title_elem.inner_text().strip() if title_elem.is_visible() else "Unknown Title"
                company = company_elem.inner_text().strip() if company_elem.is_visible() else "Unknown Company"
                location_text = location_elem.inner_text().strip() if location_elem.is_visible() else "Unknown Location"
                
                # Link handles differently for auth vs guest
                link = None
                if is_logged_in:
                    link_elem = card.locator(sel["link"]).first
                    if link_elem.is_visible():
                        link = link_elem.get_attribute("href")
                        if link and link.startswith("/"):
                            link = "https://www.linkedin.com" + link
                else:
                    link_elem = card.locator(sel["link"])
                    if link_elem.is_visible():
                        link = link_elem.get_attribute("href")

                if not link or "Unknown" in title:
                    logger.debug(f"Card {i} incomplete: Title={title}, Link={link}. Skipping.")
                    continue

                job_data = {
                    "platform": "LinkedIn",
                    "title": title,
                    "company": company,
                    "location": location_text,
                    "link": link
                }
                
                # Basic Keyword Filter (Exclude)
                if any(ex.lower() in title.lower() for ex in self.config.profile.keywords.exclude):
                    logger.info(f"Skipping {title} (Exclude keyword match)")
                    continue

                logger.info(f"Successfully extracted: {title} at {company}")
                self.results.append(job_data)
                
            except Exception as e:
                logger.debug(f"Error extracting card {i}: {e}")
                pass

        return self.results

    def check_for_captcha(self, platform: str):
        """Checks if a CAPTCHA or security challenge is visible and notifies the user."""
        captcha_indicators = [
            "iframe[src*='hcaptcha']",
            "iframe[src*='recaptcha']",
            "div.g-recaptcha",
            "#captcha-internal",
            "text='verify you're a human'",
            "text='verifique que você é um humano'",
            "text='security check'",
            "#challenge-running"
        ]
        
        for selector in captcha_indicators:
            try:
                if self.page.locator(selector).is_visible():
                    logger.warning(f"CAPTCHA detected on {platform}!")
                    screenshot_path = f"data/captcha_{platform.lower()}_{int(time.time())}.png"
                    self.page.screenshot(path=screenshot_path)
                    
                    # Notify via Telegram (we'll need to pass the notifier or import it)
                    from src.notifications import TelegramNotifier
                    notifier = TelegramNotifier(self.config)
                    notifier.notify_captcha(screenshot_path, platform)
                    return True
            except:
                continue
        return False

    def activate_antigravity_mode(self):
        """
        Activates the 'Google Gravity' experiment and causes chaos.
        Authorized by user for fun/demo purposes.
        """
        if not self.page:
            logger.warning("Browser not started. Starting for Antigravity...")
            self.start_browser()
            
        logger.info("🌌 ACTIVATING ANTIGRAVITY PROTOCOLS...")
        try:
            # 1. Navigate to Google Gravity
            url = "https://mrdoob.com/projects/chromeexperiments/google-gravity/"
            self.page.goto(url)
            time.sleep(2)
            
            # 2. Click to trigger gravity
            # The experiment usually waits for a click or movement to activate 
            self.page.mouse.click(640, 360) # Click center
            time.sleep(1)
            
            # 3. Create Chaos (Drag and Drop simulation)
            viewport_size = self.page.viewport_size
            width = viewport_size['width']
            height = viewport_size['height']
            
            for _ in range(20): # 20 random throws
                start_x = random.randint(100, width - 100)
                start_y = random.randint(100, height - 100)
                end_x = random.randint(100, width - 100)
                end_y = random.randint(100, height - 100)
                
                # Drag...
                self.page.mouse.move(start_x, start_y)
                self.page.mouse.down()
                # ...and Throw! (Fast move)
                self.page.mouse.move(end_x, end_y, steps=5) 
                self.page.mouse.up()
                
                time.sleep(0.5)
                
            logger.info("Antigravity chaos complete.")
            
        except Exception as e:
            logger.error(f"Antigravity failed: {e}")



    def run(self):
        """Main execution method for searcher (convenience)."""
        all_jobs = []
        try:
            self.start_browser()
            if self.config.platforms.linkedin.enabled:
                all_jobs.extend(self.search_linkedin())
            return all_jobs
        except Exception as e:
            logger.error(f"Job search failed: {e}")
            raise
        finally:
            self.stop_browser()

if __name__ == "__main__":
    # Test Run
    from src.config import load_config
    cfg = load_config("config/settings.yaml")
    # Force headful for debug
    cfg.bot.headless = False 
    searcher = JobSearcher(cfg)
    results = searcher.run()
    for job in results:
        print(f"- {job['title']} | {job['company']}")
