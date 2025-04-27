import yaml
import re
from typing import Dict, Any, Optional, List
from pathlib import Path
from markdown_it import MarkdownIt
import logging
from datetime import datetime
from urllib.parse import urlparse
import requests
import aiohttp
import asyncio
import io
import base64
from PIL import Image # Added back for image validation
from config import settings, Settings

from .exceptions import PublishingError, ContentValidationError # Updated import

logger = logging.getLogger(__name__)

class ContentManager:
    def __init__(self, settings: Settings, image_upload_url: Optional[str] = None):
        """
        Initializes the ContentManager with settings and an optional image upload URL.

        Args:
            settings: The application settings object.
            image_upload_url: The URL for uploading images.
        """
        self.settings = settings
        self.image_upload_url = image_upload_url
        self.default_language = self.settings.DEFAULT_LANGUAGE
        self.supported_languages = self.settings.SUPPORTED_LANGUAGES
        self.min_content_length = self.settings.MIN_CONTENT_LENGTH
        self.max_title_length = self.settings.MAX_TITLE_LENGTH
        self.max_subtitle_length = self.settings.MAX_SUBTITLE_LENGTH
        self.max_tags = self.settings.MAX_TAGS

    def parse_frontmatter(self, content: str) -> tuple[Dict[str, Any], str]:
        """Parse YAML frontmatter from markdown content using markdown-it-py."""
        md = MarkdownIt()
        # Enable frontmatter plugin if available and needed, or parse manually
        # For now, stick to manual parsing but use markdown-it for potential future enhancements
        frontmatter_pattern = r'^---\n(.*?)\n---\n(.*)$'
        match = re.match(frontmatter_pattern, content, re.DOTALL)

        if not match:
            return {}, content

        try:
            frontmatter = yaml.safe_load(match.group(1))
            content = match.group(2)
            return frontmatter, content
        except yaml.YAMLError as e:
            logger.error(f"Error parsing frontmatter: {str(e)}")
            raise ContentValidationError(f"Error parsing frontmatter: {str(e)}")

    def validate_language(self, language: str) -> str:
        """Validate and normalize language code."""
        if not language:
            return self.default_language
        
        # Normalize language code (e.g., en-US -> en)
        language = language.split('-')[0].lower()
        
        if language not in self.supported_languages:
            logger.warning(f"Unsupported language '{language}', falling back to '{self.default_language}'")
            return self.default_language
            
        return language

    def validate_frontmatter(self, frontmatter: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize frontmatter content."""
        validated = frontmatter.copy()

        # Validate language
        if 'language' in validated:
            validated['language'] = self.validate_language(validated['language'])
        else:
            validated['language'] = self.default_language

        # Validate title
        if 'title' in validated:
            self.validate_title(validated['title'])

        # Validate subtitle
        if 'subtitle' in validated:
            self.validate_subtitle(validated['subtitle'])

        # Validate tags
        if 'tags' in validated:
            self.validate_tags(validated['tags'])

        return validated

    def process_images(self, content: str, upload_images: bool = True) -> str:
        """Process markdown images, optionally uploading them."""
    async def _process_single_image(self, match: re.Match, session: aiohttp.ClientSession) -> str:
        """
        Process a single markdown image match asynchronously.

        Downloads remote images or reads local images, validates them,
        uploads them if an upload URL is provided, and returns the updated markdown.

        Args:
            match: The regex match object for the image.
            session: The aiohttp client session for making HTTP requests.

        Returns:
            The updated markdown string for the image, or the original string if processing fails.
        """
        alt_text = match.group(1)
        image_path = match.group(2)

        if not self.image_upload_url:
            # Should not happen if upload_images is False, but good safeguard
            return match.group(0)

        try:
            image_data = None
            # Handle local images
            if not urlparse(image_path).scheme:
                image_path = str(Path(image_path).resolve())
                with open(image_path, 'rb') as f:
                    image_data = f.read()
            else:
                # Handle remote images
                async with session.get(image_path) as response:
                    response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
                    image_data = await response.read()

            # Validate image format and size using PIL
            try:
                img = Image.open(io.BytesIO(image_data))
                img.verify() # Verify image integrity
                # Optional: Check image format and size
                # if img.format not in ['JPEG', 'PNG']:
                #     logger.warning(f"Unsupported image format for '{image_path}': {img.format}")
                #     return match.group(0)
                # if img.size[0] > self.settings.MAX_IMAGE_WIDTH or img.size[1] > self.settings.MAX_IMAGE_HEIGHT:
                #     logger.warning(f"Image size exceeds maximum for '{image_path}': {img.size}")
                #     return match.group(0)
            except Exception as e:
                logger.warning(f"Image validation failed for '{image_path}': {str(e)}")
                return match.group(0)

            # Upload image
            files = {'file': ('image.png', image_data)}
            async with session.post(self.image_upload_url, data=files) as response:
                response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
                result = await response.json()
                new_url = result.get('url')
            if new_url:
                return f'![{alt_text}]({new_url})'
            else:
                logger.error(f"Image upload successful but no URL returned: {response.text}")
                return match.group(0)

        except (requests.exceptions.RequestException, IOError) as e:
            logger.error(f"Error processing or uploading image '{image_path}': {str(e)}")
            return match.group(0)
        except Exception as e:
            # Catch any other unexpected errors
            logger.error(f"An unexpected error occurred processing image '{image_path}': {str(e)}")
            return match.group(0)

    async def process_images(self, content: str, upload_images: bool = True) -> str:
        """
        Process markdown images asynchronously, optionally uploading them.

        Finds all images in the markdown content, processes them concurrently,
        and replaces the original image markdown with the results.

        Args:
            content: The markdown content.
            upload_images: Whether to upload images or just keep the original links.

        Returns:
            The markdown content with processed images.
        """
        if not upload_images or not self.image_upload_url:
            return content

        image_pattern = r'!\[(.*?)\]\((.*?)\)'
        matches = list(re.finditer(image_pattern, content))
        
        if not matches:
            return content

        async with aiohttp.ClientSession() as session:
            tasks = [self._process_single_image(match, session) for match in matches]
            processed_images = await asyncio.gather(*tasks)

        # Replace original image markdown with processed results
        # Iterate in reverse to avoid issues with index changes
        for match, new_markdown in zip(reversed(matches), reversed(processed_images)):
            start, end = match.span()
            content = content[:start] + new_markdown + content[end:]

        return content

    async def validate_content(self, content: str) -> bool:
        """
        Validate markdown content asynchronously.

        Checks for minimum content length, basic structure, and broken links.

        Args:
            content: The markdown content.

        Returns:
            True if the content is valid, False otherwise.
        """
        # Check for minimum content length
        if len(content.strip()) < self.min_content_length:
            logger.warning(f"Content is too short (minimum {self.min_content_length} characters)")
            return False

        # Check for basic markdown structure
        if not re.search(r'^#\s+.+$', content, re.MULTILINE):
            logger.warning("Content missing main heading")
            return False

        # Check for broken links using markdown-it-py
        md = MarkdownIt()
        tokens = md.parse(content)
        urls = []
        for token in tokens:
            if token.type == 'link_open':
                href = token.attrGet('href')
                if href:
                    urls.append(href)

        async with aiohttp.ClientSession() as session:
            for url in urls:
                try:
                    # Use HEAD request for efficiency
                    async with session.head(url, allow_redirects=True, timeout=5) as response:
                        response.raise_for_status()
                except aiohttp.ClientError as e:
                    logger.warning(f"Broken link found: {url} - {str(e)}")
                    return False

        return True

    def sanitize_content(self, content: str) -> str:
        """Sanitize markdown content."""
        # Remove potentially harmful HTML
        content = re.sub(r'<script.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<iframe.*?</iframe>', '', content, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove excessive whitespace
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        return content

    def validate_file_path(self, file_path: str) -> None:
        """Validate that the file exists and is a markdown file"""
        if not os.path.exists(file_path):
            raise ValueError(f"File not found: {file_path}")
        if not file_path.endswith('.md'):
            raise ValueError("Only markdown (.md) files are supported")

    def validate_title(self, title: str) -> None:
        """Validate post title"""
        if not title:
            raise ValueError("Title cannot be empty")
        if len(title) > self.max_title_length:
            raise ValueError(f"Title exceeds maximum length of {self.max_title_length} characters")

    def validate_subtitle(self, subtitle: str) -> None:
        """Validate post subtitle"""
        if subtitle and len(subtitle) > self.max_subtitle_length:
            raise ValueError(f"Subtitle exceeds maximum length of {self.max_subtitle_length} characters")

    def validate_tags(self, tags: List[str]) -> None:
        """Validate post tags"""
        if len(tags) > self.max_tags:
            raise ValueError(f"Maximum {self.max_tags} tags allowed")
        for tag in tags:
            if not re.match(r'^[a-zA-Z0-9-]+$', tag):
                raise ValueError(f"Invalid tag format: {tag}")

    def read_markdown_file(self, file_path: str) -> str:
        """Read and validate markdown file content"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            if not content.strip():
                raise ValueError("File is empty")
            return content
        except UnicodeDecodeError:
            raise ValueError("File must be UTF-8 encoded")
        except Exception as e:
            raise ValueError(f"Error reading file: {str(e)}")

    async def process_markdown(self, file_path: str, upload_images: bool = True) -> tuple[Dict[str, Any], str]:
        """
        Process a markdown file asynchronously, handling frontmatter and images.

        Reads a markdown file, parses frontmatter, sanitizes content,
        processes images (optionally uploading them), and validates the content.

        Args:
            file_path: The path to the markdown file.
            upload_images: Whether to upload images found in the markdown.

        Returns:
            A tuple containing the frontmatter dictionary and the processed markdown content.

        Raises:
            ValueError: If the file path is invalid or the file is empty/not UTF-8.
            ContentValidationError: If frontmatter parsing fails.
            Exception: For other errors during processing.
        """
        try:
            # Validate file path first
            self.validate_file_path(file_path)

            content = self.read_markdown_file(file_path)

            # Parse frontmatter
            frontmatter, content = self.parse_frontmatter(content)

            # Validate and normalize frontmatter
            frontmatter = self.validate_frontmatter(frontmatter)

            # Sanitize content
            content = self.sanitize_content(content)

            # Process images if needed
            if upload_images:
                content = await self.process_images(content)

            # Validate content
            if not await self.validate_content(content):
                logger.warning(f"Content validation failed for {file_path}")

            return frontmatter, content

        except Exception as e:
            logger.error(f"Error processing markdown file: {str(e)}")
            raise

    def generate_social_media_message(self, frontmatter: Dict[str, Any], medium_link: str, substack_link: str, max_length: Optional[int] = None) -> str:
        """
        Generates a custom message for social media posts.

        Args:
            frontmatter: The frontmatter of the article.
            medium_link: The URL of the published Medium article.
            substack_link: The URL of the published Substack article.
            max_length: Optional maximum length for the message.

        Returns:
            A custom message for social media.
        """
        title = frontmatter.get('title', 'New Article')
        tags = frontmatter.get('tags', [])

        # Use summary if available, otherwise use title
        message_content = frontmatter.get('summary', title)

        # Basic message structure
        message = f"{message_content}"

        if tags:
            # Add hashtags from tags, ensuring they are valid for social media
            hashtags = " ".join([f"#{tag.replace('-', '')}" for tag in tags])
            message += f" {hashtags}"

        message += f"\n\nRead it on Medium: {medium_link}\nRead it on Substack: {substack_link}"

        # Truncate message if max_length is provided
        if max_length and len(message) > max_length:
            # Leave space for ellipsis and links
            # Calculate the length of the links part
            links_length = len(f"\n\nRead it on Medium: {medium_link}\nRead it on Substack: {substack_link}")
            available_length = max_length - links_length - 3 # -3 for ellipsis

            if available_length > 0:
                # Truncate the message content part
                truncated_content = message_content[:available_length] + "..."
                message = f"{truncated_content}"

                if tags:
                     # Add hashtags from tags, ensuring they are valid for social media
                    hashtags = " ".join([f"#{tag.replace('-', '')}" for tag in tags])
                    # Check if adding hashtags exceeds max_length after truncation
                    if len(message) + len(f" {hashtags}") <= max_length - links_length:
                         message += f" {hashtags}"
                    else:
                         # If hashtags don't fit, just add ellipsis to content
                         message = f"{message_content[:max_length - links_length - 3]}..."

                message += f"\n\nRead it on Medium: {medium_link}\nRead it on Substack: {substack_link}"

            else:
                # If no space for content, just provide links
                message = f"Read it on Medium: {medium_link}\nRead it on Substack: {substack_link}"


        return message
