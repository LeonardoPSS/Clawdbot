from src.config import load_config, Settings
from src.job_searcher import JobSearcher
from src.linkedin_booster import LinkedInBooster
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("🤝 Manually triggering LinkedIn Network Boost...")
    
    config = load_config()
    # FORCE HEADFUL FOR DEBUGGING
    config.bot.headless = False
    
    searcher = JobSearcher(config)
    searcher.start_browser()
    
    from src.linkedin_manager import LinkedInManager
    linkedin_manager = LinkedInManager(searcher.page, config)

    booster = LinkedInBooster(linkedin_manager)
    
    # Run Networking Strategy (Connect with Recruiters)
    result = booster.run_smart_networking_strategy()
    print(f"RESULT: {result}")
    
    # Keep open briefly
    import time
    time.sleep(10)
    searcher.stop_browser()

if __name__ == "__main__":
    main()
