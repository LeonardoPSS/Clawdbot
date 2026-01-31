"""
Advanced LinkedIn Engagement Functions
Standalone functions for commenting, following, and image upload
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def comment_on_relevant_posts(li_manager, limit: int = 5) -> bool:
    """Comments on relevant posts using AI-generated comments."""
    try:
        from src.content_generator import ContentGenerator
        content_gen = ContentGenerator(li_manager.config)
        
        logger.info(f"Starting intelligent commenting on {limit} posts...")
        li_manager.page.goto("https://www.linkedin.com/feed/", wait_until="load")
        li_manager.behavior.random_delay(3, 5)

        posts = li_manager.page.locator(".feed-shared-update-v2").all()
        commented = 0
        
        for i, post in enumerate(posts[:limit * 3]):
            if commented >= limit:
                break
            
            try:
                # SKIP: User's own posts or sponsored ads
                is_sponsored = post.locator(".feed-shared-actor__sub-description:has-text('Promovido'), .feed-shared-actor__sub-description:has-text('Sponsored')").first.is_visible()
                is_self = post.locator(".feed-shared-actor__name:has-text('Leonardo')").first.is_visible() # User's name
                
                if is_sponsored or is_self:
                    continue

                post_text_elem = post.locator(".feed-shared-text").first
                if not post_text_elem.is_visible():
                    continue

                
                post_text = post_text_elem.inner_text()
                comment_text = content_gen.generate_comment(post_text)
                if not comment_text:
                    continue
                
                comment_btn = post.locator("button:has-text('Comentar'), button:has-text('Comment')").first
                if comment_btn.is_visible():
                    comment_btn.click()
                    li_manager.behavior.random_delay(2, 3)
                    
                    comment_box = post.locator("div[role='textbox'], .ql-editor").first
                    if comment_box.is_visible():
                        li_manager.behavior.simulate_human_typing(comment_box, comment_text)
                        li_manager.behavior.random_delay(1, 2)
                        
                        submit_btn = post.locator("button.comments-comment-box__submit-button").first
                        if submit_btn.is_visible() and not submit_btn.is_disabled():
                            submit_btn.click()
                            logger.info(f"Commented on post {commented + 1}: {comment_text[:50]}...")
                            commented += 1
                            li_manager.behavior.random_delay(5, 10)
            except Exception as e:
                logger.warning(f"Failed to comment on post {i}: {e}")
                continue
        
        logger.info(f"Commented on {commented} posts successfully.")
        return True
    except Exception as e:
        logger.error(f"Commenting failed: {e}")
        return False

def follow_interesting_profiles(li_manager, limit: int = 10) -> bool:
    """Follows profiles based on target criteria."""
    try:
        target_titles = ["Recruiter", "HR Manager", "Tech Lead"]
        if hasattr(li_manager.config, 'linkedin_automation'):
            target_titles = li_manager.config.linkedin_automation.engagement.target_profiles
        
        logger.info(f"Searching for {limit} interesting profiles to follow...")
        followed = 0
        
        for title in target_titles:
            if followed >= limit:
                break
            
            import urllib.parse
            query = urllib.parse.quote(title)
            url = f"https://www.linkedin.com/search/results/people/?keywords={query}"
            
            li_manager.page.goto(url, wait_until="load")
            li_manager.behavior.random_delay(3, 5)
            
            follow_buttons = li_manager.page.locator("button:has-text('Seguir'), button:has-text('Follow')").all()
            
            for btn in follow_buttons[:min(3, limit - followed)]:
                try:
                    if btn.is_visible():
                        btn.click()
                        followed += 1
                        logger.info(f"Followed profile {followed}/{limit}")
                        li_manager.behavior.random_delay(3, 6)
                except:
                    continue
        
        logger.info(f"Followed {followed} profiles successfully.")
        return True
    except Exception as e:
        logger.error(f"Following profiles failed: {e}")
        return False

def upload_image_to_post(li_manager, image_path: str) -> bool:
    """Uploads an image to the LinkedIn post modal."""
    try:
        # Click the image upload button in the modal
        # Selectors can vary, 'Adicionar mídia' or similar
        image_btn_selectors = [
            "button[aria-label*='Adicionar mídia']",
            "button[aria-label*='Add media']",
            "button[aria-label*='Adicionar imagem']",
            "button[aria-label*='Add image']",
            ".share-promoted-detour-button-container button"
        ]
        
        image_btn = None
        for sel in image_btn_selectors:
            btn = li_manager.page.locator(sel).first
            if btn.is_visible():
                image_btn = btn
                break
        
        if image_btn:
            image_btn.click()
            li_manager.behavior.random_delay(2, 3)
            
            # File input is usually hidden
            file_input = li_manager.page.locator("input[type='file']").first
            file_input.set_input_files(image_path)
            li_manager.behavior.random_delay(5, 7)
            
            # Click 'Done' or 'Concluído' if needed
            done_btn = li_manager.page.locator("button:has-text('Concluído'), button:has-text('Done'), button:has-text('Próximo')").first
            if done_btn.is_visible():
                done_btn.click()
                li_manager.behavior.random_delay(2, 3)
            
            logger.info(f"Image uploaded successfully: {image_path}")
            return True
        else:
            logger.warning("No image upload button found in modal.")
            return False
    except Exception as e:
        logger.error(f"Image upload failed: {e}")
        return False

