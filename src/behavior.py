import time
import random
import math
from playwright.sync_api import Page
from src.config import Settings

class HumanBehavior:
    def __init__(self, page: Page, config: Settings):
        self.page = page
        self.config = config

    def random_delay(self, min_s: float = None, max_s: float = None):
        """Sleeps for a random amount of time."""
        if not min_s:
            min_s = self.config.behavior.action_delay_seconds.min
        if not max_s:
            max_s = self.config.behavior.action_delay_seconds.max
        
        delay = random.uniform(min_s, max_s)
        time.sleep(delay)

    def simulate_human_typing(self, selector: str, text: str):
        """Types text with random delays between keystrokes."""
        element = self.page.locator(selector)
        element.click()
        
        for char in text:
            # Random delay between 50ms and 150ms
            delay = random.uniform(
                self.config.behavior.typing_delay_ms.min, 
                self.config.behavior.typing_delay_ms.max
            )
            element.type(char, delay=delay) 

    def smooth_scroll(self):
        """Simulates smooth scrolling down the page."""
        if not self.config.behavior.scroll_simulation:
            return

        total_height = self.page.evaluate("document.body.scrollHeight")
        viewport_height = self.page.viewport_size['height']
        current_scroll = 0

        while current_scroll < total_height:
            scroll_step = random.randint(300, 700)
            current_scroll += scroll_step
            self.page.evaluate(f"window.scrollTo(0, {current_scroll})")
            time.sleep(random.uniform(0.5, 1.5))
            
            # Occasionally scroll back up a bit
            if random.random() < 0.2:
                back = random.randint(100, 300)
                current_scroll -= back
                self.page.evaluate(f"window.scrollTo(0, {current_scroll})")
                time.sleep(random.uniform(0.5, 1.0))
            
            total_height = self.page.evaluate("document.body.scrollHeight") # Update in case of infinite scroll
            if current_scroll > total_height: # Break if end
                break

    def random_mouse_move(self):
        """Simulates random mouse movements."""
        # This is a bit tricky in Playwright specific coordinates without a target
        # so we just move to center and wiggle
        vw = self.page.viewport_size['width']
        vh = self.page.viewport_size['height']
        
        self.page.mouse.move(random.randint(0, vw), random.randint(0, vh))
        time.sleep(random.uniform(0.1, 0.5))
        self.page.mouse.move(random.randint(0, vw), random.randint(0, vh))
