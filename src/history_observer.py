import os
import sqlite3
import shutil
import logging
import json
import requests
from datetime import datetime, timedelta
from src.config import load_config

logger = logging.getLogger("HistoryObserver")

class HistoryObserver:
    def __init__(self, config_path="config/settings.yaml"):
        self.config = load_config(config_path)
        self.knowledge_path = "data/user_knowledge.md"
        self.openai_api_key = self.config.secrets.openai.get("api_key") if self.config.secrets else None
        
        # Chrome history path on Windows
        self.history_path = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\Default\History")
        self.temp_history = os.path.join("data", "History_Copy")

    def _copy_history(self):
        try:
            os.makedirs("data", exist_ok=True)
            if os.path.exists(self.history_path):
                # Copying to avoid "database is locked" error while Chrome is open
                shutil.copy2(self.history_path, self.temp_history)
                return True
            else:
                logger.error(f"Chrome history file not found at {self.history_path}")
                return False
        except Exception as e:
            logger.error(f"Failed to copy history file: {e}")
            return False

    def get_recent_research(self):
        if not self._copy_history():
            return []

        recent_urls = []
        try:
            conn = sqlite3.connect(self.temp_history)
            cursor = conn.cursor()
            
            # Query for domains related to research and ChatGPT
            # last_visit_time is in WebKit format (microseconds since Jan 1, 1601)
            time_threshold = (datetime.now() - timedelta(days=2))
            webkit_threshold = int((time_threshold - datetime(1601, 1, 1)).total_seconds() * 1000000)

            query = """
            SELECT title, url, last_visit_time FROM urls 
            WHERE (url LIKE '%chatgpt.com%' OR url LIKE '%search.brave.com%' OR url LIKE '%google.com/search%' OR url LIKE '%stackoverflow.com%')
            AND last_visit_time > ?
            ORDER BY last_visit_time DESC LIMIT 30
            """
            
            cursor.execute(query, (webkit_threshold,))
            rows = cursor.fetchall()
            
            for title, url, visit_time in rows:
                if title and len(title) > 5:
                    recent_urls.append(f"{title} ({url[:50]}...)")
            
            conn.close()
            # Clean up copy
            os.remove(self.temp_history)
            
        except Exception as e:
            logger.error(f"Error querying history database: {e}")
            
        return recent_urls

    def synthesize_knowledge(self, research_data):
        if not research_data or not self.openai_api_key:
            logger.warning("No research data found or OpenAI key missing.")
            return
            
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.openai_api_key}", "Content-Type": "application/json"}
        
        prompt = f"""
        Analise o histórico de navegação recente do Leonardo e resuma seus focos de interesse atuais, projetos e tópicos de pesquisa.
        Crie um resumo estruturado para que uma IA (o Clawdbot) possa usar para agir de forma mais alinhada com ele.
        
        Histórico Recente:
        {chr(10).join(research_data)}
        
        Target format (Markdown):
        - **Principais Temas:** [Breve resumo]
        - **Projetos em Foco:** [Lista de possíveis projetos]
        - **Atitude/Interesse:** [Ex: Técnico, Curioso, Negócios, etc]
        """
        
        data = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": prompt}]
        }
        
        try:
            logger.info("Synthesizing user knowledge with OpenAI...")
            response = requests.post(url, headers=headers, json=data)
            insights = response.json()["choices"][0]["message"]["content"]
            self._save_knowledge(insights)
            logger.info("User knowledge updated successfully.")
        except Exception as e:
            logger.error(f"Failed to synthesize knowledge: {e}")

    def _save_knowledge(self, insights):
        os.makedirs("data", exist_ok=True)
        with open(self.knowledge_path, "w", encoding="utf-8") as f:
            f.write(f"# Leonardo's Personal Context\n*Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
            f.write(insights)

    def run(self):
        logger.info("Starting History-based User Learning...")
        research_data = self.get_recent_research()
        if research_data:
            logger.info(f"Found {len(research_data)} relevant research entries.")
            self.synthesize_knowledge(research_data)
        else:
            logger.info("No relevant recent research history found.")

if __name__ == "__main__":
    observer = HistoryObserver()
    observer.run()
