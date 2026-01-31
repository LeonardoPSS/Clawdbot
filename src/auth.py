import logging
import time
import random
from playwright.sync_api import Page
from src.config import Settings
from src.behavior import HumanBehavior

logger = logging.getLogger(__name__)

class Authenticator:
    def __init__(self, page: Page, config: Settings):
        self.page = page
        self.config = config
        self.behavior = HumanBehavior(page, config)

    def login_linkedin(self) -> bool:
        """Performs login on LinkedIn."""
        if not self.config.secrets or not self.config.secrets.linkedin:
            logger.error("LinkedIn credentials not found in secrets.yaml")
            return False

        creds = self.config.secrets.linkedin
        email = creds.get("email")
        password = creds.get("password")

        if not email or not password or email == "seu-email@exemplo.com":
            logger.warning("LinkedIn credentials are empty or default. Skipping login.")
            return False

        try:
            logger.info("Starting LinkedIn login check...")
            # Use a longer timeout and "load" instead of "networkidle" which can be flaky
            self.page.goto("https://www.linkedin.com/feed/", wait_until="load", timeout=60000)
            self.behavior.random_delay(3, 5)
            
            # Simple autonomy check for initial cookies/terms
            try:
                for btn_txt in ['Aceitar', 'Accept', 'Concordo', 'Ok']:
                    btn = self.page.locator(f"button:has-text('{btn_txt}')").first
                    if btn.is_visible(timeout=1000):
                        btn.click()
                        self.behavior.random_delay(1, 2)
            except: pass


            # Check if we are already logged in (Feed visible)
            if self.page.locator(".global-nav").is_visible() or "feed" in self.page.url:
                logger.info("Already logged in! Skipping login form.")
                return True

            logger.info("Not logged in. Navigating to login page...")
            self.page.goto("https://www.linkedin.com/login")
            self.behavior.random_delay(2, 4)

            # Fill email (Wait for selector with a shorter timeout if we expect it)
            self.page.wait_for_selector("input#username", timeout=10000)
            self.behavior.simulate_human_typing("input#username", email)
            self.behavior.random_delay(1, 2)

            # Fill password
            self.behavior.simulate_human_typing("input#password", password)
            self.behavior.random_delay(1, 2)

            # Click Sign In
            self.page.click("button[type='submit']")
            self.behavior.random_delay(4, 6)

            # Simple check if login was successful
            if "checkpoint" in self.page.url:
                logger.warning("Captcha or Verification detected! Please solve it manually in the browser.")
                # We could wait here for user to solve
                time.sleep(30) 

            # Give extra time for the dashboard to load
            time.sleep(5) 
            
            is_logged_in = (
                self.page.locator(".global-nav").is_visible() or 
                self.page.locator("input.search-global-typeahead__input").is_visible() or
                "feed" in self.page.url
            )

            if is_logged_in:
                logger.info("Login successful!")
                return True
            else:
                logger.error(f"Login might have failed. Current URL: {self.page.url}")
                return False

        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False
