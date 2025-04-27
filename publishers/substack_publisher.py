import logging
from typing import Dict, Any, Optional, List

from content_manager import ContentManager
from exceptions import PublishingError, ContentValidationError # Assuming exceptions are in exceptions.py

logger = logging.getLogger(__name__)

class SubstackPublisher:
    """
    Handles preparing content for manual publishing to Substack.
    Since Substack doesn't have a public API, this class focuses on
    processing content and generating instructions.
    """
    def __init__(self, content_manager: ContentManager):
        self.content_manager = content_manager

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