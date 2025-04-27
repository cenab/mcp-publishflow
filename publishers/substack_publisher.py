import logging
from typing import Dict, Any, Optional, List

from playwright.sync_api import sync_playwright, BrowserContext, Page

from content_manager import ContentManager
from exceptions import PublishingError, ContentValidationError # Assuming exceptions are in exceptions.py
from config import config # Import config for credentials and settings

logger = logging.getLogger(__name__)

class SubstackPublisher:
    """
    Handles automated content publishing to Substack via browser automation.
    """
    def __init__(self, content_manager: ContentManager):
        self.content_manager = content_manager
        self.substack_url = "https://substack.com" # Base Substack URL
        self.login_url = f"{self.substack_url}/account/login"
        self.new_post_url = f"{self.substack_url}/publish/post"
        self.username = config.SUBSTACK_USERNAME # Get credentials from config
        self.password = config.SUBSTACK_PASSWORD
        self.browser_type = config.PLAYWRIGHT_BROWSER # Get browser type from config
        self.headless = config.PLAYWRIGHT_HEADLESS # Get headless setting from config

    def publish_automated(self, file_path: str, title: str, subtitle: str = "", is_paid: bool = False, language: str = None) -> str:
        """
        Publishes content to Substack automatically using Playwright.

        Args:
            file_path: Path to the markdown file
            title: Post title
            subtitle: Optional subtitle
            is_paid: Whether the post is for paid subscribers
            language: Language code (e.g., 'en', 'es', 'fr')
        Returns:
            URL of the published post or a success message.
        """
        try:
            frontmatter, content = self.content_manager.process_markdown(file_path)

            if not language and 'language' in frontmatter:
                language = frontmatter['language']
            elif not language:
                 language = self.content_manager.default_language

            with sync_playwright() as p:
                browser = p[self.browser_type].launch(headless=self.headless)
                context = browser.new_context()
                page = context.new_page()

                self._login(page)
                post_url = self._create_and_publish_post(page, title, subtitle, content, is_paid, language)

                browser.close()

            logger.info(f"Published content to Substack: {title}")
            return post_url if post_url else "Post published successfully (URL not captured)."

        except (ContentValidationError, PublishingError) as e:
            logger.error(f"Error publishing content to Substack: {str(e)}")
            raise # Re-raise the exception after logging
        except Exception as e:
            logger.error(f"An unexpected error occurred while publishing to Substack: {str(e)}")
            raise # Re-raise the exception after logging

    def _login(self, page: Page):
        """Logs into Substack."""
        logger.info("Attempting to log in to Substack...")
        page.goto(self.login_url)

        try:
            # Fill in email and password
            page.fill('input[name="email"]', self.username) # TODO: Verify selector
            page.fill('input[name="password"]', self.password) # TODO: Verify selector

            # Click login button
            page.click('button[type="submit"]') # TODO: Verify selector

            # Wait for navigation after login
            page.wait_for_url(self.substack_url) # Wait for redirect after login
            logger.info("Successfully logged in to Substack.")

        except Exception as e:
            logger.error(f"Substack login failed: {str(e)}")
            raise PublishingError(f"Substack login failed: {str(e)}")

    def _create_and_publish_post(self, page: Page, title: str, subtitle: str, content: str, is_paid: bool, language: str) -> Optional[str]:
        """Creates a new post and publishes it."""
        logger.info(f"Attempting to create and publish post: {title}")
        page.goto(self.new_post_url)

        try:
            # Fill in title and subtitle
            page.fill('input[placeholder="Title"]', title) # TODO: Verify selector
            page.fill('input[placeholder="Subtitle"]', subtitle) # TODO: Verify selector

            # Fill in content (assuming a rich text editor or markdown area)
            # This selector is highly likely to be incorrect and needs verification
            page.fill('.editor-content', content) # TODO: Verify selector for content area

            # Handle is_paid setting
            if is_paid:
                # TODO: Add Playwright steps to mark post as paid
                logger.warning("Automated setting for 'is_paid' is not implemented yet.")

            # Handle language setting (Substack might not have a direct language setting per post via UI)
            if language and language != self.content_manager.default_language:
                 logger.warning(f"Automated setting for language '{language}' is not implemented yet.")
                 # TODO: Add Playwright steps if Substack UI allows setting language per post

            # Click publish button
            # This selector is highly likely to be incorrect and needs verification
            page.click('button:has-text("Publish")') # TODO: Verify selector for publish button

            # Wait for publishing to complete and get the post URL
            # This is a placeholder and needs actual logic to get the URL
            page.wait_for_selector('a.post-link') # Example: Wait for a link to the new post
            post_url = page.url # This might not be the final post URL, needs verification

            logger.info(f"Post creation and publishing steps completed for: {title}")
            return post_url

        except Exception as e:
            logger.error(f"Substack post creation/publishing failed for '{title}': {str(e)}")
            raise PublishingError(f"Substack post creation/publishing failed for '{title}': {str(e)}")

    # The original prepare_post method can be kept or removed depending on need.
    # Keeping it for now as it might be used elsewhere for manual instructions.
    def prepare_post(self, file_path: str, title: str, subtitle: str = "", is_paid: bool = False, language: str = None) -> str:
        """
        Prepares content for manual publishing to Substack.

        Args:
            file_path: Path to the markdown file
            title: Post title
            subtitle: Optional subtitle
            is_paid: Whether the post is for paid subscribers
            language: Language code (e.g., 'en', 'es', 'fr')
        Returns:
            Instructions for manual publishing
        """
        try:
            # Process markdown content using ContentManager
            frontmatter, content = self.content_manager.process_markdown(file_path)

            # Use language from frontmatter if not specified
            if not language and 'language' in frontmatter:
                language = frontmatter['language']
            elif not language:
                 # Use default language from content_manager settings if not in frontmatter
                 language = self.content_manager.default_language


            # Prepare content for manual publishing
            instructions = f"""
Substack Publishing Instructions:

1. Log in to your Substack dashboard
2. Click "New Post"
3. Copy and paste the following content:

Title: {title}
Subtitle: {subtitle}
Paid: {'Yes' if is_paid else 'No'}
Language: {language}

Content:
{content}

Note: You'll need to manually:
- Format the content in Substack's editor
- Add any images
- Set the publication date
- Configure any additional settings
"""

            logger.info(f"Prepared content for Substack: {title}")
            return instructions
        except (ContentValidationError, PublishingError) as e:
            logger.error(f"Error preparing content for Substack: {str(e)}")
            raise # Re-raise the exception after logging
        except Exception as e:
            logger.error(f"An unexpected error occurred while preparing for Substack: {str(e)}")
            raise # Re-raise the exception after logging