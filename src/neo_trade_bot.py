import os
import json
import logging
import random
from datetime import datetime
import time

BOT_DIR = r"c:\Users\leona\Downloads\AntigravityJobBot"
TRENDS_PATH = os.path.join(BOT_DIR, "data", "market_trends.json")
TRADE_HISTORY_PATH = os.path.join(BOT_DIR, "data", "trade_history.json")
WEALTH_PATH = os.path.join(BOT_DIR, "data", "neural_wealth.json")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class NeoTradeBot:
    def __init__(self):
        self._ensure_paths()
        self.wealth = self._load_wealth()
        self.history = self._load_history()

    def _ensure_paths(self):
        os.makedirs(os.path.dirname(TRADE_HISTORY_PATH), exist_ok=True)

    def _load_wealth(self):
        if os.path.exists(WEALTH_PATH):
            with open(WEALTH_PATH, "r") as f:
                return json.load(f)
        return {"balance": 1000.0, "total_roi": 0.0, "active_positions": []}

    def _load_history(self):
        if os.path.exists(TRADE_HISTORY_PATH):
            with open(TRADE_HISTORY_PATH, "r") as f:
                return json.load(f)
        return []

    def _save_data(self):
        with open(WEALTH_PATH, "w") as f:
            json.dump(self.wealth, f, indent=4)
        with open(TRADE_HISTORY_PATH, "w") as f:
            json.dump(self.history[-100:], f, indent=4)

    def run_cycle(self):
        logging.info("Starting NeoTrade cycle...")
        if not os.path.exists(TRENDS_PATH):
            logging.warning("No market trends found. Skipping trade cycle.")
            return

        with open(TRENDS_PATH, "r") as f:
            trends = json.load(f)

        bullish_trends = [t for t in trends if t.get("sentiment") == "Bullish"]
        
        # 1. Update Active Positions
        new_positions = []
        for pos in self.wealth["active_positions"]:
            # Simulate a 2% variance in ROI per cycle
            change = random.uniform(-0.01, 0.03) 
            pos["current_value"] *= (1 + change)
            pos["roi"] = (pos["current_value"] - pos["entry_price"]) / pos["entry_price"] * 100
            
            # Close position if it hits 15% profit or 5% loss (simulated)
            if pos["roi"] > 15 or pos["roi"] < -5:
                pos["exit_time"] = datetime.now().isoformat()
                pos["final_roi"] = pos["roi"]
                self.wealth["balance"] += pos["current_value"]
                self.history.append(pos)
                logging.info(f"Closed position: {pos['title']} | ROI: {pos['roi']:.2f}%")
            else:
                new_positions.append(pos)

        self.wealth["active_positions"] = new_positions

        # 2. Open New Positions (if balance allows and bullish trends exist)
        for trend in bullish_trends:
            # Check if already in this position
            if any(p["title"] == trend["title"] for p in self.wealth["active_positions"]):
                continue

            if self.wealth["balance"] >= 100:
                amount = 100.0
                self.wealth["balance"] -= amount
                new_pos = {
                    "title": trend["title"],
                    "entry_price": amount,
                    "current_value": amount,
                    "roi": 0.0,
                    "entry_time": datetime.now().isoformat(),
                    "sentiment": trend["sentiment"],
                    "score": trend.get("score", 50)
                }
                self.wealth["active_positions"].append(new_pos)
                logging.info(f"Opened new position: {trend['title']}")

        # Update total ROI
        self._save_data()
        logging.info(f"Cycle complete. Balance: ${self.wealth['balance']:.2f}")

if __name__ == "__main__":
    bot = NeoTradeBot()
    bot.run_cycle()
