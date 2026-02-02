import os
import json
import time
import random
import logging
import requests
from datetime import datetime
from src.config import load_config
from src.notifications import TelegramNotifier

logger = logging.getLogger("MoltbookAutonomous")

class MoltbookBot:
    def __init__(self, config_path="config/settings.yaml"):
        self.config = load_config(config_path)
        self.notifier = TelegramNotifier(self.config)
        self.api_base = "https://www.moltbook.com/api/v1"
        self.credentials_path = os.path.expanduser("~/.config/moltbook/credentials.json")
        self.knowledge_path = os.path.join(os.getcwd(), "data", "user_knowledge.md")
        self.last_post_file = os.path.join(os.getcwd(), "data", "last_moltbook_posts.json")
        self.api_key = self._load_api_key()
        self.brave_api_key = self.config.secrets.brave.get("api_key") if self.config.secrets else None
        self.openai_api_key = self.config.secrets.openai.get("api_key") if self.config.secrets else None
        
        self.automation = self.config.moltbook_automation

    def _load_api_key(self):
        try:
            if os.path.exists(self.credentials_path):
                with open(self.credentials_path, 'r') as f:
                    data = json.load(f)
                    return data.get("api_key")
        except Exception as e:
            logger.error(f"Error loading Moltbook credentials: {e}")
        return os.environ.get("MOLTBOOK_API_KEY")

    def api_call(self, method, endpoint, data=None):
        url = f"{self.api_base}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        try:
            if method == "GET":
                response = requests.get(url, headers=headers)
            else:
                response = requests.post(url, headers=headers, json=data)
            return response.json()
        except Exception as e:
            logger.error(f"API call failed to {endpoint}: {e}")
            return None

    def get_latest_news(self, query="AI agents technology news"):
        if not self.brave_api_key:
            return []
        
        url = "https://api.search.brave.com/res/v1/web/search"
        headers = {"Accept": "application/json", "X-Subscription-Token": self.brave_api_key}
        params = {"q": query, "count": 5}
        
        try:
            response = requests.get(url, headers=headers, params=params)
            results = response.json().get("web", {}).get("results", [])
            return results
        except Exception as e:
            logger.error(f"Brave Search failed: {e}")
            return []

    def generate_content(self, prompt):
        if not self.openai_api_key:
            return "Beep boop! Autonomous thinking mode engaged."

        # Load user knowledge context
        user_context = ""
        if os.path.exists(self.knowledge_path):
            with open(self.knowledge_path, "r", encoding="utf-8") as f:
                user_context = f.read()
            
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.openai_api_key}", "Content-Type": "application/json"}
        
        system_prompt = "You are Clawdbot, an advanced AI agent on Moltbook. You are professional but friendly, focused on technology and automation. Keep it concise (max 280 chars)."
        if user_context:
            system_prompt += f"\n\nContext about your owner (Leonardo):\n{user_context}\nAlways try to align your thoughts with his current interests and projects mentioned above."

        data = {
            "model": "gpt-4",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        }
        try:
            response = requests.post(url, headers=headers, json=data)
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            return None

    def interact_with_feed(self):
        logger.info("Checking Moltbook feed...")
        feed = self.api_call("GET", "/posts?sort=hot&limit=5")
        if not feed or not feed.get("success"):
            return

        posts = feed.get("posts", [])
        news_for_user = []

        for post in posts:
            if random.random() < 0.3: # 30% chance to comment
                prompt = f"React to this Moltbook post: '{post.get('title')}' - {post.get('content')}"
                comment = self.generate_content(prompt)
                if comment:
                    self.api_call("POST", f"/posts/{post.get('id')}/comments", {"content": comment})
                    logger.info(f"Commented on post {post.get('id')}")
            
            news_for_user.append({
                "title": post.get("title"),
                "author": post.get("author_name"),
                "karma": post.get("upvotes", 0)
            })

        return news_for_user

    def _get_pending_slots(self):
        if not self.automation or not self.automation.daily_posts.enabled:
            return []
            
        now = datetime.now()
        today_str = now.strftime("%Y-%m-%d")
        
        # Load posting history
        history = {}
        if os.path.exists(self.last_post_file):
            try:
                with open(self.last_post_file, "r") as f:
                    history = json.load(f)
            except:
                history = {}
        
        posted_today = history.get(today_str, [])
        
        # Use 'times' list if available, otherwise fallback to single 'time'
        target_times = self.automation.daily_posts.times
        if not target_times and self.automation.daily_posts.time:
            target_times = [self.automation.daily_posts.time]
            
        pending = []
        for t_str in target_times:
            if t_str in posted_today:
                continue
                
            sched_time = datetime.strptime(t_str, "%H:%M").replace(
                year=now.year, month=now.month, day=now.day
            )
            
            if now >= sched_time:
                pending.append(t_str)
        
        return pending

    def _mark_as_posted(self, slot_time):
        now = datetime.now()
        today_str = now.strftime("%Y-%m-%d")
        
        history = {}
        if os.path.exists(self.last_post_file):
            try:
                with open(self.last_post_file, "r") as f:
                    history = json.load(f)
            except:
                pass
        
        if today_str not in history:
            # Cleanup old dates to keep file small (keep only last 7 days)
            dates = sorted(list(history.keys()))
            if len(dates) > 7:
                for d in dates[:-7]:
                    del history[d]
            history[today_str] = []
            
        if slot_time not in history[today_str]:
            history[today_str].append(slot_time)
            
        with open(self.last_post_file, "w") as f:
            json.dump(history, f, indent=2)

    def share_news(self, force=False):
        pending_slots = self._get_pending_slots() if not force else ["forced"]
        if not pending_slots:
            return

        # Choose a topic from config
        topics = self.automation.daily_posts.topics if self.automation else ["AI and Automation"]

        # Handle all pending slots
        for slot in pending_slots:
            logger.info(f"Processing post slot: {slot}")
            topic = random.choice(topics)
            news = self.get_latest_news(query=f"{topic} latest news")
            if not news:
                continue

            item = random.choice(news)
            prompt = f"Crie um post interessante para o Moltbook baseado nesta notícia: {item.get('title')} - {item.get('description')}. Inclua o link: {item.get('url')}. Fale sobre como isso impacta o Nexus."
            content = self.generate_content(prompt)
            
            if content:
                # Use submolt 'nexus' as specified in previous version
                res = self.api_call("POST", "/posts", {"title": item.get('title'), "content": content, "submolt": "nexus"})
                if res and res.get("success"):
                    logger.info(f"Shared news for slot {slot}: {item.get('title')}")
                    if slot != "forced":
                        self._mark_as_posted(slot)

    def run_cycle(self):
        try:
            logger.info(f"--- Cycle started at {datetime.now()} ---")
            
            # Interact with feed
            moltbook_news = self.interact_with_feed()
            
            # Post new content if scheduled
            self.share_news()

            # Update user via Telegram
            if moltbook_news and self.notifier.enabled:
                message = "🗞️ Moltbook Digest:\n\n"
                for item in moltbook_news[:3]:
                    message += f"• {item['title']} (por {item['author']}) 🦞\n"
                self.notifier.send_message(message)

            logger.info("Cycle finished. Next check in 30 minutes.")
        except Exception as e:
            logger.error(f"Error in autonomous cycle: {e}")


    def start(self):
        logger.info("🚀 Clawdbot Moltbook Autonomy Started!")
        while True:
            self.run_cycle()
            time.sleep(3600) # Wait 1 hour

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="Run a single cycle and exit")
    args = parser.parse_args()

    bot = MoltbookBot()
    if args.once:
        bot.run_cycle()
    else:
        bot.start()
