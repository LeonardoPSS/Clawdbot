import os
import json
import logging
import time
import random
from typing import List, Dict
from playwright.sync_api import Page
from src.config import load_config
from src.job_searcher import JobSearcher
from src.linkedin_manager import LinkedInManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("B2BOutreach")

class B2BOutreachEngine:
    def __init__(self, config_path="config/settings.yaml"):
        self.config = load_config(config_path)
        self.searcher = JobSearcher(self.config)
        self.history_file = "data/b2b_outreach_history.json"
        self.contacted_leads = self._load_history()
        self.pitch = (
            "Olá! Notei sua atuação no setor condominial. Estamos lançando o Nexus Delivery, "
            "um SaaS que automatiza a gestão de encomendas com protocolos digitais e fotos. "
            "Gostaria de conectar e talvez agendar uma demo rápida de 5 min?"
        )

    def _load_history(self) -> List[str]:
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r") as f:
                    return json.load(f)
            except: return []
        return []

    def _save_history(self):
        os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
        with open(self.history_file, "w") as f:
            json.dump(self.contacted_leads, f, indent=4)

    def run(self, keyword="Síndico Profissional", limit=5):
        logger.info(f"🚀 Iniciando prospecção B2B para: {keyword}")
        try:
            self.searcher.start_browser()
            manager = LinkedInManager(self.searcher.page, self.config)
            
            # 1. Search for profiles
            import urllib.parse
            url = f"https://www.linkedin.com/search/results/people/?keywords={urllib.parse.quote(keyword)}"
            logger.info(f"Navegando para busca: {url}")
            self.searcher.page.goto(url, wait_until="networkidle")
            time.sleep(5)
            
            # 2. Extract results
            profiles = []
            items = self.searcher.page.locator("li.reusable-search__result-container")
            count = items.count()
            logger.info(f"Encontrados {count} perfis potenciais.")
            
            for i in range(min(count, limit * 2)): # Search broad to filter history
                if len(profiles) >= limit: break
                try:
                    item = items.nth(i)
                    name_elem = item.locator("span[aria-hidden='true']").first
                    link_elem = item.locator("a.app-aware-link").first
                    
                    if name_elem.is_visible() and link_elem.is_visible():
                        link = link_elem.get_attribute("href")
                        # Clean link to use as UID
                        uid = link.split("?")[0].rstrip("/")
                        
                        if uid in self.contacted_leads:
                            logger.info(f"Ignorando lead já contatado: {name_elem.inner_text().strip()}")
                            continue

                        profile = {
                            "uid": uid,
                            "name": name_elem.inner_text().strip(),
                            "link": link
                        }
                        profiles.append(profile)
                except: continue

            # 3. Send requests
            for p in profiles:
                logger.info(f"Enviando convite para: {p['name']}")
                success = manager.send_connection_request(
                    {"name": p['name'], "link": p['link'], "company": "Syndic/Condo"},
                    self.pitch
                )
                if success:
                    self.contacted_leads.append(p['uid'])
                    self._save_history()
                
                time.sleep(random.uniform(30, 60)) # Safety delay

            logger.info(f"🎯 Ciclo de prospecção concluído. Novos leads: {len(profiles)}")

        except Exception as e:
            logger.error(f"Erro na prospecção B2B: {e}")
        finally:
            self.searcher.stop_browser()

if __name__ == "__main__":
    engine = B2BOutreachEngine()
    # For demo run, limit to 2
    engine.run(limit=2)
