import logging
import time
import random
from typing import Optional, List, Dict
from playwright.sync_api import Page
from src.config import Settings
from src.behavior import HumanBehavior
from src.ai_assistant import AIAssistant

logger = logging.getLogger(__name__)

class LinkedInManager:
    def __init__(self, page: Page, config: Settings):
        self.page = page
        self.config = config
        self.behavior = HumanBehavior(page, config)
        self.ai = AIAssistant(config)

    def check_and_accept_popups(self):
        """Proactively checks for and clicks 'Accept', 'OK', 'Agree' buttons."""
        try:
            # Common selectors for cookies, terms, save password, etc.
            accept_selectors = [
                "button:has-text('Aceitar tudo')",
                "button:has-text('Aceitar todos os cookies')",
                "button:has-text('Accept all')",
                "button:has-text('Concordo')",
                "button:has-text('I agree')",
                "button:has-text('Ok')",
                "button:has-text('Entendi')",
                "button:has-text('Got it')",
                "button:has-text('Permitir')",
                "button:has-text('Allow')",
                ".artdeco-button--primary:has-text('Aceitar')",
                ".artdeco-button--primary:has-text('Accept')"
            ]
            
            for sel in accept_selectors:
                try:
                    btn = self.page.locator(sel).first
                    if btn.is_visible(timeout=500):
                        logger.info(f"Proactive Autonomy: Clicking '{sel}'")
                        btn.click(force=True)
                        self.behavior.random_delay(1, 2)
                except: continue
                
            # Specifically handle the "Sync contacts" or "Save password" overlays if they appear
            overlays = self.page.locator(".artdeco-modal, .ip-fuse-limit-alert__header").all()
            for ov in overlays:
                if ov.is_visible():
                    # Look for a close or dismiss button inside the modal
                    dismiss = ov.locator("button[aria-label*='dismiss'], button[aria-label*='fechar'], button:has-text('Pular'), button:has-text('Skip')").first
                    if dismiss.is_visible():
                        logger.info("Proactive Autonomy: Dismissing modal overlay.")
                        dismiss.click()
                        self.behavior.random_delay(1, 2)
        except Exception as e:
            logger.debug(f"Popup check minor issue: {e}")

    def generate_professional_post(self, resume_context: str) -> Optional[str]:

        """Generates a professional LinkedIn post using AI."""
        keywords = ", ".join(self.config.behavior.evolution.engagement_keywords)
        
        system_prompt = (
            "You are a professional social media manager for a job seeker. "
            "Write a short, engaging LinkedIn post (3-5 sentences) about professional growth, "
            "industry trends, or a quick tip related to the candidate's area. "
            "Include 2-3 relevant hashtags. "
            "The tone should be professional yet approachable. "
            "Language must be Portuguese (pt-BR)."
        )
        
        user_prompt = (
            f"Candidate Keywords: {keywords}\n"
            f"Candidate Profile: {self.config.profile.role} at {self.config.profile.level} level.\n"
            f"Resume Highlights: {resume_context[:500]}...\n\n"
            "Generate the post content now:"
        )
        
        logger.info("Generating AI post content for LinkedIn...")
        return self.ai.ask_gpt(system_prompt, user_prompt)

    def create_post(self, content: str, image_path: Optional[str] = None) -> bool:
        """Navigates to LinkedIn and publishes a post with an optional image."""

        try:
            logger.info("Starting post creation on LinkedIn...")
            self.page.goto("https://www.linkedin.com/feed/", wait_until="networkidle", timeout=60000)
            self.page.bring_to_front()
            self.behavior.random_delay(8, 12) 
            
            # Autonomy: Clear any initial popups
            self.check_and_accept_popups()

            # 0. Close Messaging Overlays
            try:
                msg_bar = self.page.locator("section.msg-overlay-list-bubble, [aria-label='Mensagens']")
                if msg_bar.is_visible():
                    logger.info("Minimizing messaging area...")
                    msg_bar.locator("header").click(force=True)
                    self.behavior.random_delay(2, 4)
            except: pass


            # 1. Click "Start a post" / "Começar publicação"
            trigger_selectors = [
                ".share-box-feed-entry__trigger",
                "button.share-mb__trigger",
                "button:has-text('Começar publicação')",
                "span:has-text('Começar publicação')",
                "button:has-text('Start a post')",
                "span:has-text('Start a post')",
                "div[role='button']:has-text('Começar publicação')",
                "div[role='button']:has-text('Start a post')",
                ".artdeco-button--tertiary.share-box-feed-entry__trigger",
                "button[aria-label='Começar publicação']",
                "button[aria-label='Start a post']"
            ]
            
            post_trigger = None
            for sel in trigger_selectors:
                try:
                    btn = self.page.locator(sel).first
                    if btn.is_visible():
                        logger.info(f"Targeting post trigger: {sel}")
                        post_trigger = btn
                        break
                except: continue
            
            if not post_trigger:
                # Last resort: look for the text anywhere in a clickable element
                try:
                    logger.info("Trying last resort text selector...")
                    post_trigger = self.page.get_by_text("Começar publicação", exact=False).first
                    if not post_trigger.is_visible():
                        post_trigger = self.page.get_by_text("Start a post", exact=False).first
                except: pass

            if not post_trigger or not post_trigger.is_visible():
                logger.error("Step 1 Failed: 'Start post' trigger not found.")
                self.page.screenshot(path="data/debug_post_step1_trigger_not_found.png")
                return False

            logger.info("Found post trigger. Clicking...")
            post_trigger.hover()
            post_trigger.click(force=True)
            self.behavior.random_delay(3, 5)


            # 2. Wait for the modal/dialog
            modal_selectors = ["div[role='dialog']", ".artdeco-modal", ".share-box-entry"]
            modal = None
            for m_sel in modal_selectors:
                if self.page.locator(m_sel).first.is_visible():
                    modal = self.page.locator(m_sel).first
                    break
            
            if not modal:
                logger.error("Step 2 Failed: Modal did not appear.")
                return False

            logger.info("Post modal is visible.")
            
            # Handle Image Upload if provided
            if image_path:
                logger.info(f"Image provided: {image_path}. Attempting upload...")
                from src.linkedin_advanced import upload_image_to_post
                upload_image_to_post(self, image_path)
                self.behavior.random_delay(2, 3)

            editor_sel = ".ql-editor, div[role='textbox'], [aria-label='Texto da publicação']"
            editor = modal.locator(editor_sel).first
            
            if not editor.is_visible():
                editor = modal.locator("div[role='textbox'], .ql-editor").first

            logger.info("Typing content...")
            editor.click()
            editor.fill(content)
            self.behavior.random_delay(1, 2)
            editor.type(" ", delay=100)
            
            self.behavior.random_delay(2, 3)

            # 3. Click the button (could be 'Next' or 'Post' depending on UI)
            # We look for 'Next' or 'Post' inside the modal
            post_published = False  # Flag to prevent duplicate posts
            for step in range(2): # Max 2 steps if 'Next' exists
                if post_published:  # Skip if already published
                    break
                    
                btn_selectors = [
                    "button.share-actions__primary-action",
                    "button:has-text('Publicar')",
                    "button:has-text('Post')",
                    "button.share-box_post-button",
                    "button:has-text('Próximo')",
                    "button:has-text('Next')",
                    "button:has-text('Avançar')",
                    ".artdeco-button--primary" # High risk but often the post button
                ]
                
                action_btn = None
                logger.info(f"Step 3.{step}: Looking for action button...")
                for btn_sel in btn_selectors:
                    try:
                        btn = modal.locator(btn_sel).first
                        if btn.is_visible():
                            btn_text = btn.inner_text().strip()
                            logger.info(f"Step 3.{step}: Found candidate action button: '{btn_text}' with selector '{btn_sel}'")
                            action_btn = btn
                            break
                    except: continue

                
                if not action_btn:
                    logger.error(f"Step 3.{step} Failed: No action button found in modal.")
                    self.page.screenshot(path=f"data/debug_post_step3_{step}.png")
                    break

                if action_btn.is_disabled():
                    logger.warning(f"Button '{btn_text}' is disabled. Waiting...")
                    self.behavior.random_delay(2, 4)

                action_btn.click()
                logger.info(f"Clicked '{btn_text}'")
                self.behavior.random_delay(2, 3)

                # If the button we clicked was 'Post' or 'Publicar', we are done
                if any(t in btn_text.lower() for t in ["post", "publicar", "enviar"]):
                    post_published = True
                    logger.info("✅ Post button clicked - marking as published")
                    break
            
            # 4. Success Verification (Redirection or Modal Closing)
            try:
                # Wait for modal to close
                self.page.wait_for_selector("div[role='dialog'], .artdeco-modal", state="hidden", timeout=15000)
                logger.info("Modal closed. Checking for success...")
                
                # Check for success toast
                success_indicators = [
                    ".artdeco-toast-item",
                    ":has-text('Publicação enviada')",
                    ":has-text('Post successful')",
                    ":has-text('Sua publicação foi compartilhada')"
                ]
                for ind in success_indicators:
                    if self.page.locator(ind).first.is_visible():
                        logger.info(f"✅ Success indicator found: {ind}")
                        break
            except Exception as e:
                logger.warning(f"Verification wait failed: {e}")

            # FINAL VERIFICATION: Go to activity feed and check
            logger.info("Navigating to Profile Activity for final verification...")
            self.page.goto("https://www.linkedin.com/in/", wait_until="networkidle")
            current_url = self.page.url.rstrip("/")
            if "/in/" not in current_url:
                # If we are not on a specific profile page, try to find the link to our own profile
                try:
                    profile_link = self.page.locator("a.ember-view.block[href*='/in/']").first
                    if profile_link.is_visible():
                        current_url = profile_link.get_attribute("href")
                        if current_url.startswith("/"): current_url = "https://www.linkedin.com" + current_url
                except: pass
            
            # The most reliable activity URL for personal shares
            activity_url = f"{current_url.rstrip('/')}/recent-activity/shares/"
            logger.info(f"Checking activity at: {activity_url}")
            self.page.goto(activity_url, wait_until="load")
            self.behavior.random_delay(8, 12)

            
            # Strict check: find the first post in activity and check if snippet matches
            # The posts are usually inside .feed-shared-update-v2
            first_post = self.page.locator(".feed-shared-update-v2, .profile-creator-shared-feed-update__container").first
            if first_post.is_visible():
                post_text = first_post.inner_text().lower()
                snippet = content.strip().lower()[:20]
                if snippet in post_text:
                    logger.info("🎯 VERIFIED: Post is live on your profile!")
                    return True
            
            logger.warning("🔎 Post not found in 'Recent Activity' top item. It might have failed.")
            self.page.screenshot(path="data/final_post_verification_failed_v2.png")
            return False

        except Exception as e:
            logger.error(f"Post creation EXCEPTION: {e}")
            self.page.screenshot(path="data/debug_post_crash.png")
            return False

    def engage_with_feed(self, limit: int = 5):
        """Likes and engages with posts in the feed to increase visibility."""
        try:
            logger.info(f"Starting engagement cycle on LinkedIn feed (limit: {limit})...")
            self.page.goto("https://www.linkedin.com/feed/", wait_until="load", timeout=60000)
            self.behavior.random_delay(3, 5)
            
            # Autonomy: Clear popups before engaging
            self.check_and_accept_popups()


            for i in range(limit):
                self.behavior.smooth_scroll()
                self.behavior.random_delay(1, 3)

                # VERY STRICT Like button selector to avoid Repost/Share
                # The Like button has a specific class and usually says "Gostar" or "Like"
                # We target the button that is NOT a repost/share button
                like_btn_sel = (
                    "button.react-button__trigger:has-text('Gostar'), "
                    "button.react-button__trigger:has-text('Like'), "
                    "button[aria-label^='Gostar de'], "
                    "button[aria-label^='Like ']"
                )
                
                buttons = self.page.locator(like_btn_sel)
                count = buttons.count()
                
                if count > i:
                    btn = buttons.nth(i)
                    # Avoid clicking "Share" or "Repost" buttons that might match text
                    aria_label = (btn.get_attribute("aria-label") or "").lower()
                    if "repost" in aria_label or "compartilhar" in aria_label:
                        logger.debug(f"Skipping button {i+1} - detected as Repost/Share.")
                        continue

                    if btn.is_visible() and "artdeco-button--muted" in (btn.get_attribute("class") or ""):
                        logger.info(f"Liking post {i+1}...")
                        btn.click()
                        self.behavior.random_delay(2, 4)
                    else:
                        logger.debug(f"Post {i+1} already liked or not clickable.")
                
            logger.info("Engagement cycle finished.")
            return True

        except Exception as e:
            logger.error(f"Engagement failed: {e}")
            return False

    def search_recruiters(self, company_name: str) -> List[Dict]:
        """Searches for recruiters at a specific company."""
        try:
            query = f"Recrutador {company_name}"
            import urllib.parse
            url = f"https://www.linkedin.com/search/results/people/?keywords={urllib.parse.quote(query)}"
            
            logger.info(f"Searching for recruiters at {company_name}: {url}")
            self.page.goto(url, wait_until="load")
            self.behavior.random_delay(3, 5)

            recruiters = []
            # Selector for search result items
            result_selectors = [
                 "li.reusable-search__result-container",
                 ".search-results-container li"
            ]
            
            # Use multiple selectors
            items = None
            for sel in result_selectors:
                if self.page.locator(sel).count() > 0:
                    items = self.page.locator(sel)
                    break
            
            if not items:
                logger.warning(f"No recruiters found for {company_name}")
                return []

            for i in range(min(items.count(), 3)):
                item = items.nth(i)
                name_elem = item.locator("span[aria-hidden='true']").first
                link_elem = item.locator("a.app-aware-link").first
                
                if name_elem.is_visible() and link_elem.is_visible():
                    recruiters.append({
                        "name": name_elem.inner_text().strip(),
                        "link": link_elem.get_attribute("href"),
                        "company": company_name
                    })
            
            return recruiters

        except Exception as e:
            logger.error(f"Recruiter search failed: {e}")
            return []

    def send_connection_request(self, recruiter: Dict, resume_context: str) -> bool:
        """Sends a personalized connection request to a recruiter."""
        try:
            logger.info(f"Attempting to connect with recruiter: {recruiter['name']}")
            self.page.goto(recruiter['link'], wait_until="load")
            self.behavior.random_delay(3, 5)

            # Look for "Connect" button
            connect_btn = self.page.locator("button:has-text('Conectar'), button:has-text('Connect')").first
            if not connect_btn.is_visible():
                # Check under "More" menu
                more_btn = self.page.locator("button:has-text('Mais'), button:has-text('More')").first
                if more_btn.is_visible():
                    more_btn.click()
                    self.behavior.random_delay(1, 2)
                    connect_btn = self.page.locator("div[role='button']:has-text('Conectar'), div[role='button']:has-text('Connect')").first

            if not connect_btn or not connect_btn.is_visible():
                logger.warning(f"Connect button not found for {recruiter['name']}")
                return False

            connect_btn.click()
            self.behavior.random_delay(2, 3)

            # AI Note Generation
            system_prompt = (
                "You are writing a short, professional LinkedIn connection request note (max 300 characters). "
                "The target is a recruiter. Mention that you applied for a position and would love to connect. "
                "The note must be polite and in Portuguese (pt-BR)."
            )
            user_prompt = f"Recruiter: {recruiter['name']}\nCompany: {recruiter['company']}\nCandidate Area: {self.config.profile.area}\n\nWrite the note:"
            note = self.ai.ask_gpt(system_prompt, user_prompt)
            
            if note and len(note) <= 300:
                # Click "Add a note"
                add_note_btn = self.page.locator("button:has-text('Adicionar nota'), button:has-text('Add a note')").first
                if add_note_btn.is_visible():
                    add_note_btn.click()
                    self.behavior.random_delay(1, 2)
                    self.behavior.simulate_human_typing("textarea[name='message']", note)
                    self.behavior.random_delay(1, 2)
                    
                    # Click Send
                    send_btn = self.page.locator("button:has-text('Enviar'), button:has-text('Send')").first
                    send_btn.click()
                    logger.info(f"Connection request sent to {recruiter['name']} with note.")
                    return True

            # If note fails or too long, just send without note if button exists
            send_without_note = self.page.locator("button:has-text('Enviar sem nota'), button:has-text('Send without a note')").first
            if send_without_note.is_visible():
                send_without_note.click()
                logger.info(f"Connection request sent to {recruiter['name']} WITHOUT note.")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to send connection request: {e}")
            return False

    def search_and_engage(self, keywords: List[str], limit_per_keyword: int = 2):
        """Searches for posts by keywords and engages with them."""
        try:
            import urllib.parse
            for kw in keywords:
                url = f"https://www.linkedin.com/search/results/content/?keywords={urllib.parse.quote(kw)}&sortBy=%22date_posted%22"
                logger.info(f"Visibility Engine: Engaging with posts for '{kw}'...")
                self.page.goto(url, wait_until="load")
                self.behavior.random_delay(3, 5)

                like_buttons = self.page.locator("button.react-button__trigger:has-text('Gostar'), button.react-button__trigger:has-text('Like')")
                
                count = like_buttons.count()
                for i in range(min(count, limit_per_keyword)):
                    btn = like_buttons.nth(i)
                    if btn.is_visible() and "artdeco-button--muted" in btn.get_attribute("class"):
                        # Scroll to button
                        btn.scroll_into_view_if_needed()
                        self.behavior.random_delay(1, 2)
                        logger.info(f"Targeted Liking: '{kw}' post {i+1}...")
                        btn.click()
                        self.behavior.random_delay(2, 4)
            
            return True

        except Exception as e:
            logger.error(f"Targeted engagement failed: {e}")
            return False

    def check_connections_and_message(self):
        """Checks for recently accepted connections and sends a follow-up message."""
        try:
            logger.info("Checking for new connections to send follow-up messages...")
            self.page.goto("https://www.linkedin.com/mynetwork/invite-connect/connections/", wait_until="load")
            self.behavior.random_delay(3, 5)

            # Look for the first few connections
            connections = self.page.locator("li.mn-connection-card")
            count = connections.count()
            
            for i in range(min(count, 3)):
                card = connections.nth(i)
                name = card.locator(".mn-connection-card__details .mn-connection-card__name").inner_text().strip()
                
                # Check if we already messaged this person (simplified check)
                # For a production bot, we'd use a database. Here we'll just check if the "Message" button exists.
                msg_btn = card.locator("button:has-text('Mensagem'), button:has-text('Message')").first
                if msg_btn.is_visible():
                    logger.info(f"Found new connection: {name}. Preparing follow-up...")
                    msg_btn.click()
                    self.behavior.random_delay(2, 3)
                    
                    # AI Message Generation
                    system_prompt = (
                        "You are writing a short, professional LinkedIn message to a recruiter who just accepted your connection request. "
                        "Mention that you are interested in opportunities at their company and thanks for connecting. "
                        "Language: Portuguese (pt-BR)."
                    )
                    user_prompt = f"Recruiter Name: {name}\n\nWrite the message:"
                    message = self.ai.ask_gpt(system_prompt, user_prompt)
                    
                    if message:
                        editor = self.page.locator("div[role='textbox'], .msg-form__contenteditable").first
                        if editor.is_visible():
                            self.behavior.simulate_human_typing(editor, message)
                            self.behavior.random_delay(1, 2)
                            # send_btn = self.page.locator("button.msg-form__send-button").first
                            # send_btn.click()
                            logger.info(f"Follow-up message prepared for {name}. (Sending automated)")
                            # For safety in this MVP, we might just type it and let user click send or automate it:
                            self.page.keyboard.press("Control+Enter") 
                            time.sleep(2)
            
            return True

        except Exception as e:
            logger.error(f"Follow-up check failed: {e}")
            return False

    def perform_profile_audit(self) -> str:
        """Analyzes the user's profile and provides AI suggestions."""
        try:
            logger.info("Performing Profile Audit...")
            self.page.goto("https://www.linkedin.com/in/", wait_until="load") # Redirects to self
            self.behavior.random_delay(3, 5)

            # Extract Headline and About
            headline = self.page.locator("div.text-body-medium.break-words").inner_text().strip()
            # about_section = self.page.locator("#about").parent().locator(".display-flex").inner_text().strip()
            
            system_prompt = (
                "You are an expert LinkedIn profile auditor. Analyze the following profile headline "
                "and provide 3 specific tips to make it more attractive to recruiters in the candidate's field. "
                "Language: Portuguese (pt-BR)."
            )
            user_prompt = f"Headline: {headline}\nTarget Role: {self.config.profile.role}\n\nTips:"
            tips = self.ai.ask_gpt(system_prompt, user_prompt)
            return tips or "Nenhuma sugestão no momento."

        except Exception as e:
            logger.error(f"Profile audit failed: {e}")
            return "Erro ao realizar auditoria."
