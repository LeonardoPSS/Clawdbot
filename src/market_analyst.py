import os
import json
import logging
import requests
from src.config import load_config

logger = logging.getLogger("MarketAnalyst")

class MarketAnalyst:
    def __init__(self, config_path="config/settings.yaml"):
        self.config = load_config(config_path)
        self.brave_api_key = self.config.secrets.brave.get("api_key") if self.config.secrets else None
        self.trends_path = "data/market_trends.json"

    def scan_market(self):
        if not self.brave_api_key:
            logger.error("Brave API Key missing for market scan.")
            return []

        queries = [
            "top trending micro-saas ideas 2026",
            "common automation pain points for small businesses",
            "most requested AI agents functionality in 2026",
            "GitHub trending projects AI automation"
        ]

        all_trends = []
        for query in queries:
            url = "https://api.search.brave.com/res/v1/web/search"
            headers = {"Accept": "application/json", "X-Subscription-Token": self.brave_api_key}
            params = {"q": query, "count": 10}
            
            try:
                response = requests.get(url, headers=headers, params=params)
                results = response.json().get("web", {}).get("results", [])
                for res in results:
                    all_trends.append({
                        "title": res.get("title"),
                        "description": res.get("description"),
                        "url": res.get("url"),
                        "source_query": query
                    })
            except Exception as e:
                logger.error(f"Scan failed for '{query}': {e}")

        # Save trends to JSON
        os.makedirs("data", exist_ok=True)
        
        # Add Sentiment pass (The Oráculo)
        scored_trends = self._score_trends(all_trends)
        
        with open(self.trends_path, "w", encoding="utf-8") as f:
            json.dump(scored_trends, f, indent=4)
        
        logger.info(f"Market scan complete. Found {len(scored_trends)} leads with sentiment scoring.")
        return scored_trends

    def _score_trends(self, trends):
        if not trends: return []
        # Simulate sentiment scoring for now (could be an LLM call)
        # We'll use keyword analysis as a lightweight 'Oráculo'
        bullish_keywords = ["growth", "top", "best", "trending", "requested"]
        
        for trend in trends:
            content = (trend["title"] + trend["description"]).lower()
            score = 0
            for kw in bullish_keywords:
                if kw in content: score += 20
            
            trend["sentiment"] = "Bullish" if score > 20 else "Neutral"
            trend["sentiment_score"] = min(score + 40, 95) # Artificial base score for aesthetics
            
        return trends

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    analyst = MarketAnalyst()
    analyst.scan_market()
