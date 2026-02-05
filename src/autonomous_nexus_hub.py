import os
import time
import subprocess
import logging

# Configure integrated logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [NEXUS-HUB] - %(levelname)s - %(message)s')
logger = logging.getLogger("NexusHub")

class NexusAutonomousHub:
    def __init__(self):
        self.b2b_path = r"c:\Users\leona\Downloads\AntigravityJobBot"
        self.trade_path = r"c:\Users\leona\Downloads\NeoTradeBot_FINAL_CORRIGIDO\NeoTradeBot_FINAL"
        self.processes = {}

    def start_engines(self):
        logger.info("Initializing Nexus Autonomous Hub (Sales Only)...")
        
        # 1. Start B2B Outreach (Sales Engine)
        logger.info("Activating Nexus Delivery B2B Sales Engine...")
        self.processes['b2b'] = subprocess.Popen(
            ["python", "-m", "src.b2b_outreach"],
            cwd=self.b2b_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

    def monitor(self):
        logger.info("Monitoring Nexus Sales Operations...")
        try:
            while True:
                for name, proc in self.processes.items():
                    if proc.poll() is not None:
                        logger.warning(f"Engine {name} stopped. Exit code: {proc.returncode}")
                        # Optionally restart B2B here if it was turned into a daemon
                
                time.sleep(60)
        except KeyboardInterrupt:
            logger.info("Shutting down Nexus Hub...")
            for proc in self.processes.values():
                proc.terminate()

if __name__ == "__main__":
    hub = NexusAutonomousHub()
    hub.start_engines()
    hub.monitor()
