import requests
import logging
import time
from typing import Dict, Any, List

from exceptions import PublishingError # Assuming PublishingError is in exceptions.py

logger = logging.getLogger(__name__)

# Constants
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds

class MediumPublisher:
    def __init__(self, api_key: str, api_url: str):
        self.api_key = api_key
        self.api_url = api_url # This will need to be the correct endpoint for creating posts

    def make_api_request(self, url: str, headers: dict, payload: dict, retries: int = MAX_RETRIES) -> requests.Response:
        """Make API request with retry logic"""
        for attempt in range(retries):
            try:
                response = requests.post(url, json=payload, headers=headers)
                if response.status_code == 429:  # Rate limit
                    if attempt < retries - 1:
                        logger.warning(f"Rate limited, retrying in {RETRY_DELAY} seconds...")
                        time.sleep(RETRY_DELAY)
                        continue
                response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
                return response
            except requests.exceptions.RequestException as e:
                if attempt < retries - 1:
                    logger.warning(f"Request failed, retrying in {RETRY_DELAY} seconds...")
                    time.sleep(RETRY_DELAY)
                    continue
                raise PublishingError(f"API request failed after {retries} attempts: {str(e)}")

    def publish_post(self, title: str, content: str, tags: List[str] = None, public: bool = True, language: str = None) -> str:
        """
        Publishes a post to Medium.
        Args:
            title: Post title
            content: Post content in markdown format
            tags: List of tags for the post
            public: Whether the post is public or draft
            language: Language code (e.g., 'en', 'es', 'fr')
        Returns:
            Confirmation message or error
        """
        payload = {
            "title": title,
            "contentFormat": "markdown",
            "content": content,
            "tags": tags or [],
            "language": language,
            "publishStatus": "public" if public else "draft"
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Note: The MEDIUM_API_URL defined above is likely incorrect for creating posts.
        # The correct endpoint is typically users/{authorId}/posts.
        # This will need to be updated with the correct author ID and endpoint.
        # For now, using the potentially incorrect URL for structural refactoring.
        response = self.make_api_request(self.api_url, headers, payload)

        # Assuming a successful response returns the created post details
        # The actual response structure might differ based on the correct Medium API endpoint
        post_url = response.json().get('url', 'N/A')
        return f"Successfully published to Medium. Post URL: {post_url}"