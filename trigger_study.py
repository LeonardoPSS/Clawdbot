from src.config import load_config
from src.desktop_automation import DesktopAgent
import logging
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("🧠 Manually triggering Nexara Study Session...")
    
    config = load_config()
    # Ensure headless is False for visual
    import os
    os.environ["HEADLESS_MODE"] = "false"
    
    agent = DesktopAgent(config)
    
    topics = [
        "Advanced Quantum Computing",
        "The History of Renaissance Art",
        "Bioinformatics Trends 2026",
        "Rust Programming Language Memory Safety",
        "Neurallink Brain Interfaces"
    ]
    topic = random.choice(topics)
    
    result = agent.perform_autonomous_learning(topic)
    print(f"RESULT: {result}")

if __name__ == "__main__":
    main()
