import logging
import datetime
import os
import sys
import time
import random
from src.config import load_config
from src.resume_parser import ResumeParser
from src.job_searcher import JobSearcher
from src.storage import Storage
from src.applicant import Applicant
from src.notifications import TelegramNotifier
from src.linkedin_manager import LinkedInManager
from src.auth import Authenticator

# Configure logging to stdout
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("AntigravityMaster")

def main():
    logger.info("Starting Antigravity Job Bot 🚀")
    
    # 1. Load Config
    try:
        config = load_config("config/settings.yaml")
    except Exception as e:
        logger.critical(f"Config load failed: {e}")
        return

    # 2. Prepare Storage
    storage = Storage(config.logging.save_path + "/applied.csv")

    # 3. Parse Resume (Optional verify)
    parser = ResumeParser(config.resume.file_path)
    resume_data = parser.parse()
    logger.info(f"Resume loaded for: {resume_data['extracted'].get('email', 'Unknown User')}")

    searcher = JobSearcher(config)
    
    try:
        searcher.start_browser()
        
        # 4.1 Login if secrets are provided
        auth = Authenticator(searcher.page, config)
        logged_in_li = auth.login_linkedin()
        

        # Pass the browser page to applicant
        applicant = Applicant(searcher.page, config, storage)
        
        # Initialize Notifier
        notifier = TelegramNotifier(config)
        
        # Initialize stats and counts from storage
        stats = {
            "Applied": storage.get_today_count(),
            "Already Applied": 0,
            "External (Manual)": 0,
            "Low Match": 0,
            "Failed": 0,
            "LinkedIn": 0
        }
        applications_count = stats["Applied"]
        limit = config.bot.daily_application_limit
        
        logger.info(f"Resuming with {applications_count}/{limit} applications already done today.")

        while True:
            # 4.2 LinkedIn Evolution Suite (Networking & Content)
            if config.behavior.evolution.enabled:
                logger.info("Initializing LinkedIn Evolution Suite... 👔✨")
                li_manager = LinkedInManager(searcher.page, config)
                
                # Import Content & Advanced features
                from src.content_generator import ContentGenerator
                from src.linkedin_advanced import comment_on_relevant_posts, follow_interesting_profiles
                content_gen = ContentGenerator(config)
                
                # Post Generation with varied topics (Only if not posted today)
                last_post_file = "data/last_post_date.txt"
                today_str = datetime.datetime.now().strftime("%Y-%m-%d")
                already_posted = False
                if os.path.exists(last_post_file):
                    with open(last_post_file, "r") as f:
                        if f.read().strip() == today_str:
                            already_posted = True
                
                if not already_posted:
                    post_content = content_gen.generate_varied_post(resume_data['raw_text'])
                    if post_content:
                        image_path = None
                        if config.linkedin_automation.image_generation.enabled:
                            logger.info("🎨 Generating image for post...")
                            image_path = content_gen.generate_and_save_image(post_content)
                        
                        logger.info(f"AI suggested post (Topic: {content_gen.get_daily_topic()}): {post_content[:50]}...")
                        if li_manager.create_post(post_content, image_path=image_path):
                            logger.info("✅ Post created successfully.")
                            with open(last_post_file, "w") as f:
                                f.write(today_str)
                else:
                    logger.info("Already posted today. Skipping post generation.")

                
                # Engagement
                li_manager.engage_with_feed(limit=3)
                comment_on_relevant_posts(li_manager, limit=2) # Advanced feature
                follow_interesting_profiles(li_manager, limit=5) # Advanced feature
                
                # Follow-up Messaging
                li_manager.check_connections_and_message()

            # 4.3 Job Application Loop
            if applications_count < limit:
                logger.info(f"--- Starting Search Cycle ({applications_count}/{limit} applied) ---")
                
                jobs = []
                if config.platforms.linkedin.enabled:
                    jobs.extend(searcher.search_linkedin())
                    
                logger.info(f"Found {len(jobs)} total potential jobs across platforms.")

                for job in jobs:
                    if applications_count >= limit:
                        break
                        
                    logger.info(f"Analyzing: {job['title']} [{job['platform']}]")
                    status = applicant.apply(job)
                    logger.info(f"Result: {status}")
                    
                    # Update detailed stats
                    if "APPLIED" in status and "ALREADY" not in status:
                        applications_count += 1
                        stats["Applied"] += 1
                        stats[job['platform']] += 1
                        notifier.notify_application(job, status)
                    elif "EXTERNAL" in status or "READY_TO_SUBMIT" in status:
                        stats["External (Manual)"] += 1
                        notifier.notify_manual_review(job)
                    elif "LOW_MATCH" in status:
                        stats["Low Match"] += 1
                    elif "DUPLICATE" in status or "ALREADY" in status:
                        stats["Already Applied"] += 1
                    elif "FAILED" in status or "ERROR" in status:
                        stats["Failed"] += 1
                    
                    # Random delay between jobs
                    time.sleep(random.uniform(10, 20))

            # Daily Report Summary
            print("\n" + "="*45)
            print("📊 RELATÓRIO DE ATIVIDADE")
            print(f"Total Inscritas hoje:  {stats['Applied']}")
            print("-" * 45)
            print("="*45 + "\n")

            if applications_count >= limit:
                logger.info("Daily application limit reached. Sleeping for 4 hours before next check...")
                time.sleep(60 * 60 * 4)
            else:
                logger.info("Cycle finished. Waiting 30 minutes for new vacancies...")
                time.sleep(60 * 30)
            
            # Reset count if it's a new day (simple check)
            # This is naive but works for a persistent process
            # Better way: storage.get_today_count() at start of each cycle
            applications_count = storage.get_today_count()
            stats["Applied"] = applications_count


    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
    except Exception as e:
        logger.error(f"Bot runtime error: {e}")
    finally:
        if not config.bot.headless:
            logger.info("Bot finished. Keeping browser open as requested. Close it manually or press Ctrl+C in terminal.")
            # Keep process alive so browser remains open
            try:
                while True:
                    time.sleep(60)
            except KeyboardInterrupt:
                pass
        
        searcher.stop_browser()
        logger.info("Bot finished execution.")

if __name__ == "__main__":
    main()
