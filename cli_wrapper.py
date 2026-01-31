"""
CLI Wrapper for AntigravityJobBot - Allows single-action execution
Usage: python cli_wrapper.py [action] [args]
"""
import sys
import logging
from src.config import load_config
from src.resume_parser import ResumeParser
from src.job_searcher import JobSearcher
from src.linkedin_manager import LinkedInManager
from src.auth import Authenticator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("CLIWrapper")

def main():
    if len(sys.argv) < 2:
        print("Usage: python cli_wrapper.py [post|engage|connect|audit] [content]")
        sys.exit(1)
    
    action = sys.argv[1].lower()
    
    # Load config
    config = load_config("config/settings.yaml")
    searcher = JobSearcher(config)
    
    try:
        searcher.start_browser()
        auth = Authenticator(searcher.page, config)
        auth.login_linkedin()
        
        li_manager = LinkedInManager(searcher.page, config)
        
        if action == "post":
            content = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else None
            if not content:
                parser = ResumeParser(config.resume.file_path)
                resume_data = parser.parse()
                content = li_manager.generate_professional_post(resume_data['raw_text'])
            
            if content:
                success = li_manager.create_post(content)
                print(f"POST_SUCCESS" if success else "POST_FAILED")
            else:
                print("POST_FAILED: No content")
        
        elif action == "engage":
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 5
            li_manager.engage_with_feed(limit=limit)
            print("ENGAGE_SUCCESS")
        
        elif action == "connect":
            company = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "Tech"
            recruiters = li_manager.search_recruiters(company)
            if recruiters:
                parser = ResumeParser(config.resume.file_path)
                resume_data = parser.parse()
                for rec in recruiters[:2]:
                    li_manager.send_connection_request(rec, resume_data['raw_text'])
                print(f"CONNECT_SUCCESS: {len(recruiters[:2])} requests sent")
            else:
                print("CONNECT_FAILED: No recruiters found")
        
        elif action == "audit":
            tips = li_manager.perform_profile_audit()
            print(f"AUDIT_RESULT:\n{tips}")
        
        else:
            print(f"UNKNOWN_ACTION: {action}")
    
    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"ERROR: {e}")
    finally:
        searcher.stop_browser()

if __name__ == "__main__":
    main()
