import logging
import time
import random
import unicodedata
from pathlib import Path
from playwright.sync_api import Page
from src.config import Settings
from src.storage import Storage
from src.behavior import HumanBehavior
from src.ai_assistant import AIAssistant
from src.resume_parser import ResumeParser

logger = logging.getLogger(__name__)

def normalize_text(text: str) -> str:
    """Removes accents and converts to lowercase."""
    if not text:
        return ""
    # Normalize to NFD (decomposed) and filter out non-spacing marks (accents)
    nfkd_form = unicodedata.normalize('NFKD', str(text))
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)]).lower()

class Applicant:
    def __init__(self, page: Page, config: Settings, storage: Storage):
        self.page = page
        self.config = config
        self.storage = storage
        self.behavior = HumanBehavior(page, config)

    def apply(self, job: dict) -> str:
        """
        Main application logic.
        Returns the status of the application (APPLIED, SKIPPED, FAILED).
        """
        link = job.get("link")
        if not link:
            return "FAILED"

        if self.storage.is_already_applied(link):
            logger.info(f"Skipping {job['title']} - Already applied.")
            return "SKIPPED_DUPLICATE"

        logger.info(f"Processing: {job['title']} at {job['company']}")
        
        try:
            self.page.goto(link)
            self.behavior.random_delay(2, 5) # Initial load wait
            self.behavior.random_mouse_move() # Simulate human checking page
            
            # Scroll to read description
            self.behavior.smooth_scroll()
            
            # 1. Compatibility Check (Basic Keyword Match)
            score = self.evaluate_compatibility(job)
            job["compatibility_score"] = score
            logger.info(f"Compatibility Score: {score}/100")

            if score < 20: # Example threshold
                logger.info(f"Skipping {job['title']} - Low compatibility score.")
                return "SKIPPED_LOW_MATCH"

            # 2. Find "Easy Apply" Button
            # Check if we already applied (LinkedIn shows "Applied" or similar)
            already_applied_texts = ["Candidatura enviada", "Vaga salva", "Applied", "Saved"]
            page_text = self.page.content()
            if any(t in page_text for t in already_applied_texts):
                logger.info("Page indicates this job was already applied for or saved.")
                self.storage.add_application(job, status="ALREADY_APPLIED_ON_SITE")
                return "SKIPPED_ALREADY_ON_SITE"

            # LinkedIn selectors: button.jobs-apply-button, .jobs-apply-button, [data-control-name="jobdetails_topcard_apply"]
            apply_selectors = [
                "button.jobs-apply-button",
                ".jobs-apply-button",
                "button.jobs-apply-button--top-card",
                "[data-job-id] button:has-text('Easy Apply')",
                "button:has-text('Inscrição simplificada')",
                "button:has-text('Candidatura simplificada')",
                "button:has-text('Easy Apply')"
            ]
            
            easy_apply_btn = None
            # Wait for any of the selectors to be visible
            for selector in apply_selectors:
                try:
                    btn = self.page.locator(selector).first
                    if btn.is_visible():
                        easy_apply_btn = btn
                        break
                except:
                    continue
            
            if not easy_apply_btn:
                # Last ditch effort: find ANY button that has simplified apply text
                logger.debug("Searching for any button with apply text...")
                buttons = self.page.locator("button")
                for i in range(buttons.count()):
                    btn = buttons.nth(i)
                    txt = btn.inner_text()
                    if "simplificada" in txt.lower() or "easy apply" in txt.lower():
                        easy_apply_btn = btn
                        break

            if not easy_apply_btn:
                # Check for Captcha before giving up
                from src.job_searcher import JobSearcher
                temp_js = JobSearcher(self.config)
                temp_js.page = self.page
                if temp_js.check_for_captcha("LinkedIn/Apply"):
                    logger.warning("Application flow blocked by CAPTCHA.")
                
                logger.info("No 'Easy Apply' button found. This might be an external application.")
                status = "REQUIRES_EXTERNAL"
            else:
                logger.info("'Easy Apply' detected! Starting application process...")
                
                if self.config.bot.mode == "semi-automatic":
                    user_decision = self.ask_user_confirmation(job)
                    if not user_decision:
                        return "SKIPPED_USER"

                status = self.process_easy_apply_flow()

            self.storage.add_application(job, status=status)
            return status

        except Exception as e:
            logger.error(f"Failed to process {link}: {e}")
            return "FAILED"

    def process_easy_apply_flow(self) -> str:
        """
        Clicks through the LinkedIn Easy Apply modal.
        """
        try:
            # Click the main "Apply" button to open modal
            self.page.click("button.jobs-apply-button")
            self.behavior.random_delay(3, 5)

            # Loop through steps
            max_steps = 15 # Increased to handle complex forms
            for i in range(max_steps):
                # 1. Automated Acceptance of Terms/Consent
                self.accept_terms_and_consents()
                
                # 2. Fill visible questions
                self.handle_questions()
                
                # 3. Check for "Submit" button
                submit_btn = self.page.locator("button:has-text('Enviar candidatura'), button:has-text('Submit application'), button:has-text('Finalizar')")
                if submit_btn.is_visible():
                    logger.info("Found Submit button! Finalizing automatically...")
                    submit_btn.click()
                    self.behavior.random_delay(5, 8)
                    
                    # Post-submit cleanup (closen success modal)
                    self.finalize_application_post_submit()
                    return "APPLIED_AUTO"

                # 4. Check for "Next" / "Review" button
                next_btn = self.page.locator("button:has-text('Próximo'), button:has-text('Avançar'), button:has-text('Next'), button:has-text('Review')")
                if next_btn.is_visible():
                    logger.info(f"Advancing step {i+1}...")
                    next_btn.click()
                    self.behavior.random_delay(2, 4)
                else:
                    # Check if modal is still open but no buttons found
                    if self.page.locator("div[role='dialog']").is_visible():
                        logger.warning("Modal still open but no action buttons found. Attempting emergency close.")
                        self.finalize_application_post_submit()
                    break

            return "APPLIED_PARTIAL"

        except Exception as e:
            logger.error(f"Error in Easy Apply flow: {e}")
            return "FLOW_ERROR"

    def accept_terms_and_consents(self):
        """Clicks on any consent or acceptance checkboxes/buttons."""
        try:
            # Checkboxes for consent/terms
            consent_selectors = [
                "label:has-text('Aceito'), label:has-text('I agree'), label:has-text('Concordo')",
                "input[type='checkbox']",
                "label:has-text('Accept'), label:has-text('Consent')"
            ]
            for sel in consent_selectors:
                checkboxes = self.page.locator(sel).all()
                for cb in checkboxes:
                    if cb.is_visible() and not cb.is_checked():
                        logger.info(f"Automated Consent: Clicking {sel}")
                        cb.click()
                        self.behavior.random_delay(1, 2)
        except: pass

    def finalize_application_post_submit(self):
        """Closes any success or follow-up modals after submission."""
        try:
            self.behavior.random_delay(2, 4)
            close_btn = self.page.locator("button[aria-label='Fechar'], button[aria-label='Dismiss'], button:has-text('Done'), button:has-text('Concluído')").first
            if close_btn.is_visible():
                logger.info("Closing post-application modal.")
                close_btn.click()
                self.behavior.random_delay(2, 3)
        except: pass

    def handle_questions(self):

        """
        Attempts to answer form questions automatically using a knowledge base.
        """
        import yaml
        answers_path = Path("config/answers.yaml")
        knowledge_base = {"questions": []}
        
        if answers_path.exists():
            try:
                with open(answers_path, 'r', encoding='utf-8') as f:
                    knowledge_base = yaml.safe_load(f) or knowledge_base
            except Exception as e:
                logger.error(f"Error loading answers.yaml: {e}")

        # Helper to find a smart answer based on text
        def get_smart_answer(text: str) -> Optional[str]:
            text_lower = text.lower()
            for item in knowledge_base.get("questions", []):
                if any(kw.lower() in text_lower for kw in item.get("keywords", [])):
                    return item.get("answer")
            return None

        try:
            # 1. Handle Text and Textarea Inputs
            inputs = self.page.locator("input[type='text'], input:not([type]), textarea").all()
            for inp in inputs:
                if inp.is_visible() and not inp.input_value():
                    # Look for a label or name to identify the question
                    label = self.page.locator(f"label[for='{inp.get_attribute('id')}']").first
                    question_text = label.inner_text() if label.is_visible() else (inp.get_attribute("name") or "")
                    
                    smart_val = get_smart_answer(question_text)
                    if not smart_val:
                        # Fallback to AI
                        ai = AIAssistant(self.config)
                        # We need raw text of the resume for context
                        parser = ResumeParser(self.config.resume.file_path)
                        resume_text = parser.read_file()
                        smart_val = ai.get_answer_for_question(question_text, resume_text)

                    if smart_val:
                        logger.info(f"Answer found for '{question_text[:30]}...': {smart_val}")
                        self.behavior.simulate_human_typing(inp, smart_val)
                    else:
                        # Fallback for years of experience
                        if "experience" in question_text.lower() or "anos" in question_text.lower():
                            self.behavior.simulate_human_typing(inp, "2")
                        else:
                            # Generic fallback for required fields
                            self.behavior.simulate_human_typing(inp, "1")
                    self.behavior.random_delay(1, 2)

            # 2. Handle Radio Buttons (Yes/No)
            radios = self.page.locator("label:has-text('Yes'), label:has-text('Sim')").all()
            for radio in radios:
                if radio.is_visible():
                    # Check if the question text might need a 'No/Não' (rare for eligibility)
                    parent_text = radio.evaluate("el => el.parentElement.innerText").lower()
                    if "visa" in parent_text or "patrocínio" in parent_text:
                        # For visa sponsorship, usually answer No
                        no_radio = self.page.locator("label:has-text('No'), label:has-text('Não')").first
                        if no_radio.is_visible():
                            no_radio.click()
                    else:
                        radio.click()
                    self.behavior.random_delay(1, 2)

            # 3. Handle Select Dropdowns
            selects = self.page.locator("select").all()
            for sel in selects:
                if sel.is_visible():
                    # Try to find a smart option
                    options = sel.locator("option").all()
                    question_text = sel.evaluate("el => el.parentElement.innerText")
                    smart_val = get_smart_answer(question_text)
                    
                    matched = False
                    if smart_val:
                        for opt in options:
                            if smart_val.lower() in opt.inner_text().lower():
                                sel.select_option(value=opt.get_attribute("value"))
                                matched = True
                                break
                    
                    if not matched:
                        # Fallback to AI
                        from src.ai_assistant import AIAssistant
                        ai = AIAssistant(self.config)
                        # We need raw text of the resume for context
                        from src.resume_parser import ResumeParser
                        parser = ResumeParser(self.config.resume.file_path)
                        resume_text = parser.read_file()
                        
                        ai_val = ai.get_answer_for_question(question_text, resume_text)
                        if ai_val:
                            # Try to match AI answer with options
                            for opt in options:
                                if ai_val.lower() in opt.inner_text().lower() or opt.inner_text().lower() in ai_val.lower():
                                    sel.select_option(value=opt.get_attribute("value"))
                                    matched = True
                                    break
                        
                        if not matched:
                            # Default to the second option
                            if len(options) > 1:
                                sel.select_option(index=1)
                    
                    self.behavior.random_delay(1, 2)

        except Exception as e:
            logger.debug(f"Minor issue answering questions: {e}")

    def evaluate_compatibility(self, job: dict) -> int:
        """
        Calculates a compatibility score based on keywords or AI analysis.
        """
        # Try AI First if Key exists
        from src.ai_assistant import AIAssistant
        ai = AIAssistant(self.config)
        if ai.api_key:
            from src.resume_parser import ResumeParser
            parser = ResumeParser(self.config.resume.file_path)
            resume_text = parser.read_file()
            
            # Fetch full text from page if possible for JD
            try:
                # Common JD containers
                jd_text = self.page.locator(".jobs-description__content, #jobDescriptionText, .jobsearch-JobComponent-description").inner_text()
            except:
                jd_text = job.get("title", "")
            
            score = ai.evaluate_compatibility(jd_text, resume_text)
            logger.info(f"AI Compatibility Score: {score}/100")
            return score

        # Fallback to Keyword Match
        score = 0
        raw_title = job.get('title', '')
        title_norm = normalize_text(raw_title)
        
        matches = []
        for kw in self.config.profile.keywords.include:
            kw_norm = normalize_text(kw)
            if kw_norm in title_norm:
                matches.append(kw)
                score += 30
        
        if matches:
            logger.info(f"Matches found: {', '.join(matches)}")
        
        return min(score, 100) if matches else 10

    def ask_user_confirmation(self, job: dict) -> bool:
        """
        Simulates asking the user. In a real CLI/GUI, this would be an input().
        For headless/agentic context, we might rely on pre-config or assume 'True' for 'semi' meaning 
        'log it but don't submit final button without me', but here we'll just log the prompt.
        """
        # In a real interactive run, we would use input(). 
        # But this code runs inside the agent environment where input() blocks.
        # We will assume TRUE for the sake of the 'bot' running logic, 
        # or we could make it wait for a file signal.
        
        logger.info(f"[SEMI-AUTO] Asking user: Apply to {job['title']}? (Auto-approving for demo)")
        return True

