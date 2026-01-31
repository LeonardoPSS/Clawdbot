"""
LinkedIn Automation Scheduler
Runs daily tasks: posts, engagement, follows
"""
import sys
import os
import logging
import datetime
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import load_config
from src.resume_parser import ResumeParser
from src.job_searcher import JobSearcher
from src.linkedin_manager import LinkedInManager
from src.auth import Authenticator
from src.content_generator import ContentGenerator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("LinkedInScheduler")

def run_daily_automation():
    """Runs the daily LinkedIn automation tasks."""
    logger.info("🚀 Starting LinkedIn Daily Automation")
    
    config = load_config("config/settings.yaml")
    searcher = JobSearcher(config)
    
    try:
        searcher.start_browser()
        auth = Authenticator(searcher.page, config)
        auth.login_linkedin()
        
        li_manager = LinkedInManager(searcher.page, config)
        content_gen = ContentGenerator(config)
        
        # Import advanced functions
        sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
        from linkedin_advanced import comment_on_relevant_posts, follow_interesting_profiles
        
        # 1. Daily Post with varied content
        logger.info("📝 Generating daily post...")
        parser = ResumeParser(config.resume.file_path)
        resume_data = parser.parse()
        
        post_content = content_gen.generate_varied_post(resume_data['raw_text'])
        if post_content:
            image_path = None
            if config.linkedin_automation.image_generation.enabled:
                logger.info("🎨 Generating image for post...")
                image_path = content_gen.generate_and_save_image(post_content)
            
            success = li_manager.create_post(post_content, image_path=image_path)
            logger.info(f"Post {'✅ SUCCESS' if success else '❌ FAILED'}")

        
        # 2. Engagement (likes)
        logger.info("👍 Engaging with feed...")
        li_manager.engage_with_feed(limit=config.linkedin_automation.engagement.likes_per_day)
        
        # 3. Intelligent Comments
        logger.info("💬 Commenting on posts...")
        comment_on_relevant_posts(li_manager, config.linkedin_automation.engagement.comments_per_day)
        
        # 4. Follow interesting profiles
        logger.info("👥 Following new profiles...")
        follow_interesting_profiles(li_manager, config.linkedin_automation.engagement.follows_per_day)
        
        logger.info("✅ Daily automation completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Automation failed: {e}")
    finally:
        searcher.stop_browser()

if __name__ == "__main__":
    run_daily_automation()
