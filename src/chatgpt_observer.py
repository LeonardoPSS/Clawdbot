import os
import time
import logging
import json
from datetime import datetime
from playwright.sync_api import sync_playwright
from src.config import load_config

logger = logging.getLogger("ChatGPTObserver")

class ChatGPTObserver:
    def __init__(self, config_path="config/settings.yaml"):
        self.config = load_config(config_path)
        self.knowledge_path = "data/user_knowledge.md"
        self.openai_api_key = self.config.secrets.openai.get("api_key") if self.config.secrets else None
        
    def start_browser(self, playwright):
        profile_path = os.path.abspath("browser_profile")
        context = playwright.chromium.launch_persistent_context(
            user_data_dir=profile_path,
            headless=False, # Must be false to allow user to handle first login if needed
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        return context

    def scrape_chat_titles(self):
        logger.info("Starting ChatGPT Observation...")
        titles = []
        
        with sync_playwright() as playwright:
            context = self.start_browser(playwright)
            page = context.pages[0] if context.pages else context.new_page()
            
            try:
                page.goto("https://chatgpt.com/?model=gpt-4o", wait_until="domcontentloaded", timeout=60000)
                time.sleep(5)
                
                # Check if we need login (simple check)
                if "login" in page.url or page.locator("button:has-text('Log in')").is_visible():
                    logger.warning("USER ACTION REQUIRED: Please log in to ChatGPT in the opened browser window.")
                    # Wait up to 5 minutes for login
                    try:
                        page.wait_for_selector("nav", timeout=300000) 
                        logger.info("Login detected. Proceeding...")
                    except:
                        logger.error("Login timeout. Please try running the script again.")
                        return []
                
                # Scrape history titles from sidebar
                # We try multiple common selectors for ChatGPT history items
                selectors = [
                    "ol li div a",
                    "nav ol li a",
                    "div[data-testid*='history-item'] a",
                    "a[href*='/c/']"
                ]
                
                titles = []
                found = False
                for sel in selectors:
                    try:
                        logger.info(f"Trying selector: {sel}")
                        page.wait_for_selector(sel, timeout=15000)
                        elements = page.locator(sel).all()
                        for el in elements:
                            text = el.inner_text().strip()
                            if text and len(text) > 3 and "\n" not in text:
                                titles.append(text)
                        if titles:
                            found = True
                            logger.info(f"Found {len(titles)} titles using {sel}")
                            break
                    except:
                        continue
                
                if not found:
                    logger.error("Could not find any chat history titles. ChatGPT UI might have changed.")
                
                return list(set(titles))[:20] # Return unique titles
                
            except Exception as e:
                logger.error(f"Failed to scrape ChatGPT: {e}")
            finally:
                context.close()
                
        return titles

    def synthesize_knowledge(self, titles):
        if not titles or not self.openai_api_key:
            return
            
        import requests
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.openai_api_key}", "Content-Type": "application/json"}
        
        prompt = f"""
        Analyze these recent ChatGPT conversation titles from Leonardo and summarize his current focus, interests, and projects.
        Format accurately as a markdown list of insights.
        
        Titles:
        {chr(10).join(titles)}
        
        Target format:
        - **Tema Principal:** [Descrição]
        - **Interesses Atuais:** [Lista]
        - **Humor/Vibe:** [Descrição baseada nos temas]
        """
        
        data = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": prompt}]
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            insights = response.json()["choices"][0]["message"]["content"]
            self._save_knowledge(insights)
            logger.info("User knowledge synthesized and saved.")
        except Exception as e:
            logger.error(f"Failed to synthesize knowledge: {e}")

    def _save_knowledge(self, insights):
        os.makedirs("data", exist_ok=True)
        with open(self.knowledge_path, "w", encoding="utf-8") as f:
            f.write(f"# Leonardo's Personal Context\n*Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
            f.write(insights)

    def run(self):
        titles = self.scrape_chat_titles()
        if titles:
            self.synthesize_knowledge(titles)

if __name__ == "__main__":
    observer = ChatGPTObserver()
    observer.run()
