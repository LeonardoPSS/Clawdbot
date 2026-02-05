import os
import time
import logging
import psutil
from datetime import datetime
from src.config import load_config
from src.notifications import TelegramNotifier

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SystemMonitor")

class SystemMonitor:
    def __init__(self, config_path="config/settings.yaml"):
        self.config = load_config(config_path)
        self.notifier = TelegramNotifier(self.config)
        self.log_file = "bot.log"
        self.last_pos = 0
        if os.path.exists(self.log_file):
            self.last_pos = os.path.getsize(self.log_file)

    def check_logs(self):
        if not os.path.exists(self.log_file):
            return

        with open(self.log_file, "r", encoding="utf-8", errors="ignore") as f:
            f.seek(self.last_pos)
            lines = f.readlines()
            self.last_pos = f.tell()

            for line in lines:
                if "ERROR" in line or "CRITICAL" in line:
                    self.notifier.send_message(f"🚨 CLAWDBOT ALERT: {line.strip()}")

    def check_resources(self):
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory().percent
        if cpu > 90 or ram > 90:
            self.notifier.send_message(f"⚠️ SYSTEM RESOURCE WARNING:\nCPU: {cpu}%\nRAM: {ram}%")

    def run(self):
        logger.info("🛡️ ClawdBot System Monitor Active")
        while True:
            try:
                self.check_logs()
                self.check_resources()
                time.sleep(60) # Check every minute
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                time.sleep(300)

if __name__ == "__main__":
    monitor = SystemMonitor()
    monitor.run()
