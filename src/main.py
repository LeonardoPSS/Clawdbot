import logging
from datetime import datetime
import os
import sys
import time
import random
import threading
from flask import Flask
from src.config import load_config
from src.resume_parser import ResumeParser
from src.job_searcher import JobSearcher
from src.storage import Storage
from src.applicant import Applicant
from src.notifications import TelegramNotifier
from src.linkedin_manager import LinkedInManager
from src.auth import Authenticator
from src.telegram_bot import TelegramBot
from src.moltbook_autonomous import MoltbookBot

# Configure logging to stdout
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("bot.log", mode="a", encoding="utf-8")
    ]
)
logger = logging.getLogger("AntigravityMaster")

# --- Cloud Health Check Server ---
app = Flask(__name__)

@app.route("/")
def health_check():
    return "Nexara Bot is Running! 🚀", 200

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"🌍 Starting Health Check Server on port {port}")
    # Run without debug to avoid reloader issues in thread
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
# ---------------------------------


def main():
    # 0. Start Health Check Server (Critical for Cloud)
    server_thread = threading.Thread(target=run_web_server, daemon=True)
    server_thread.start()

    logger.info("Starting Antigravity Job Bot 🚀")
    
    desktop_agent = None
    telegram_bot = None
    searcher = None

    # 1. Load Config
    try:
        config = load_config("config/settings.yaml")
    except Exception as e:
        logger.critical(f"Config load failed: {e}")
        return

    # 2. Prepare Storage
    storage = Storage(config.logging.save_path + "/applied.csv")

    # 3. Initialize Telegram Bot Early (for connectivity during setup)
    try:
        telegram_bot = TelegramBot(config)
        if config.notifications.telegram.enabled:
            telegram_bot.start()
            logger.info("🤖 Telegram Bot connection established.")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Telegram Bot: {e}")
        telegram_bot = None

    # 4. Parse Resume
    parser = ResumeParser(config.resume.file_path)
    resume_data = parser.parse()
    logger.info(f"Resume loaded for: {resume_data['extracted'].get('email', 'Unknown User')}")

    searcher = JobSearcher(config)
    
    searcher = JobSearcher(config)
    
    # Check if any job platform is enabled
    platforms_enabled = (
        config.platforms.linkedin.enabled or
        config.platforms.gupy.enabled or 
        config.platforms.vagas_com.enabled
    )
    
    try:
        if platforms_enabled:
            logger.info("Initializing Job Search Browser...")
            searcher.start_browser()
        else:
            logger.info("ℹ️ No job platforms enabled. Skipping browser launch (Headless Mode).")
            # Create a dummy page object if needed or handle None in applicant
            
        # 4.1 Login 
        if platforms_enabled:
            auth = Authenticator(searcher.page, config)
            # logged_in_li = auth.login_linkedin() # DISABLED: User requested no LinkedIn access
            logged_in_li = False
        
            # Pass the browser page to applicant
            applicant = Applicant(searcher.page, config, storage)
        else:
            applicant = None
        
        # Initialize Desktop Agent (Autonomous Control) - LinkedIn integration disabled
        desktop_agent = DesktopAgent(config, linkedin_manager=None)
        
        # Update Telegram Bot with shared instances
        telegram_bot.job_searcher = searcher
        telegram_bot.desktop_agent = desktop_agent
        
        # AUTO-START AUTONOMOUS MODE
        if config.bot.mode == "automatic":
             def telegram_callback(msg):
                 if telegram_bot and telegram_bot.allowed_chat_id:
                     telegram_bot.send_message(telegram_bot.allowed_chat_id, msg)
             
             logger.info("🧠 Auto-starting Autonomous Loop...")
             desktop_agent.start_autonomous_loop(telegram_callback)
        
        # AUTO-START AUTONOMY AS REQUESTED BY USER
        logger.info("🤖 Auto-starting Autonomous Mode...")
        telegram_bot.enable_autonomous_mode()
        
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
            # 4.2 LinkedIn Evolution Suite (DISABLED BY USER REQUEST)
            # Completely commented out to prevent execution errors
            """
            if config.behavior.evolution.enabled:
                try:
                    logger.info("Initializing LinkedIn Evolution Suite... 👔✨")
                    li_manager = LinkedInManager(searcher.page, config)
                    
                    # Import Content & Advanced features
                    from src.content_generator import ContentGenerator
                    from src.linkedin_advanced import comment_on_relevant_posts, follow_interesting_profiles
                    import datetime # Re-import to be absolutely safe against shadowing/NameError
                    
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
                except Exception as evo_e:
                    logger.error(f"⚠️ Error in LinkedIn Evolution Suite (Skipping): {evo_e}")
            """


            # 4.3 Moltbook Automation
            if config.moltbook_automation:
                try:
                    # Initialize on demand or outside loop (optimization: outside loop is better but this is safe)
                    if 'moltbook_bot' not in locals():
                        moltbook_bot = MoltbookBot()
                    
                    logger.info("Initializing Moltbook Automation... 🦞")
                    moltbook_bot.run_cycle()
                except Exception as mb_e:
                    logger.error(f"⚠️ Error in Moltbook Automation: {mb_e}")

            # 4.4 Job Application Loop
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
            logger.info("Bot finished job search tasks.")
    
            # Keep alive for autonomous mode
            if desktop_agent and desktop_agent.autonomous_active:
                logger.info("🧠 Autonomous Mode is active. Keeping system alive...")
                try:
                    while True:
                        time.sleep(60)
                except KeyboardInterrupt:
                    logger.info("Stopping...")
            else:
                logger.info("Bot finished. Keep browser open? (Press Ctrl+C to exit)")
                # Existing wait logic or exit
                try:
                    while True:
                        time.sleep(10)
                except KeyboardInterrupt:
                    pass
        
        searcher.stop_browser()
        if 'telegram_bot' in locals():
            telegram_bot.stop()

        logger.info("Bot finished execution.")

if __name__ == "__main__":
    main()
