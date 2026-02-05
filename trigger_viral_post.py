from src.config import load_config, Settings
from src.job_searcher import JobSearcher
from src.linkedin_booster import LinkedInBooster
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("🚀 Manually triggering LinkedIn Viral Post...")
    
    config = load_config()
    
    # FORCE HEADFUL FOR DEBUGGING
    config.bot.headless = False
    
    # Setup separate logger
    fh = logging.FileHandler('debug_run.log', mode='w', encoding='utf-8')
    fh.setLevel(logging.INFO)
    logging.getLogger().addHandler(fh)
    
    searcher = JobSearcher(config)
    
    searcher.start_browser()
    
    from src.linkedin_manager import LinkedInManager
    linkedin_manager = LinkedInManager(searcher.page, config)

    booster = LinkedInBooster(linkedin_manager)
    
    result = booster.run_viral_post_strategy()
    print(f"RESULT: {result}")
    
    # Keep open briefly to see result
    searcher.stop_browser()

if __name__ == "__main__":
    main()
