import yaml
import re
from typing import Dict, Any, Optional, List
from pathlib import Path
import logging
from datetime import datetime
from urllib.parse import urlparse
import requests
from PIL import Image
import io
import base64
from config import settings

from .exceptions import PublishingError, ContentValidationError # Updated import

logger = logging.getLogger(__name__)

class ContentManager:
    def __init__(self, image_upload_url: Optional[str] = None):
        self.image_upload_url = image_upload_url
        self.default_language = settings.DEFAULT_LANGUAGE
        self.supported_languages = settings.SUPPORTED_LANGUAGES
        self.min_content_length = settings.MIN_CONTENT_LENGTH
        self.max_title_length = settings.MAX_TITLE_LENGTH
        self.max_subtitle_length = settings.MAX_SUBTITLE_LENGTH
        self.max_tags = settings.MAX_TAGS

    def parse_frontmatter(self, content: str) -> tuple[Dict[str, Any], str]:
        """Parse YAML frontmatter from markdown content."""
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
            return {}, content

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
            if len(validated['title']) > self.max_title_length:
                raise ValueError(f"Title exceeds maximum length of {self.max_title_length} characters")
                
        # Validate subtitle
        if 'subtitle' in validated:
            if len(validated['subtitle']) > self.max_subtitle_length:
                raise ValueError(f"Subtitle exceeds maximum length of {self.max_subtitle_length} characters")
                
        # Validate tags
        if 'tags' in validated:
            if len(validated['tags']) > self.max_tags:
                raise ValueError(f"Maximum {self.max_tags} tags allowed")
            for tag in validated['tags']:
                if not re.match(r'^[a-zA-Z0-9-]+$', tag):
                    raise ValueError(f"Invalid tag format: {tag}")
                    
        return validated

    def process_images(self, content: str, upload_images: bool = True) -> str:
        """Process markdown images, optionally uploading them."""
        def process_image(match):
            alt_text = match.group(1)
            image_path = match.group(2)
            
            if not upload_images or not self.image_upload_url:
                return match.group(0)

            try:
                # Handle local images
                if not urlparse(image_path).scheme:
                    image_path = str(Path(image_path).resolve())
                    with open(image_path, 'rb') as f:
                        image_data = f.read()
                else:
                    # Handle remote images
                    response = requests.get(image_path)
                    image_data = response.content

                # Upload image
                files = {'file': ('image.png', image_data)}
                response = requests.post(self.image_upload_url, files=files)
                
                if response.status_code == 200:
                    new_url = response.json().get('url')
                    return f'![{alt_text}]({new_url})'
                else:
                    logger.error(f"Failed to upload image: {response.text}")
                    return match.group(0)

            except Exception as e:
                logger.error(f"Error processing image: {str(e)}")
                return match.group(0)

        # Find and process all images
        image_pattern = r'!\[(.*?)\]\((.*?)\)'
        return re.sub(image_pattern, process_image, content)

    def validate_content(self, content: str) -> bool:
        """Validate markdown content."""
        # Check for minimum content length
        if len(content.strip()) < self.min_content_length:
            logger.warning(f"Content is too short (minimum {self.min_content_length} characters)")
            return False

        # Check for basic markdown structure
        if not re.search(r'^#\s+.+$', content, re.MULTILINE):
            logger.warning("Content missing main heading")
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

    def process_markdown(self, file_path: str, upload_images: bool = True) -> tuple[Dict[str, Any], str]:
        """Process a markdown file, handling frontmatter and images."""
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
                content = self.process_images(content)

            # Validate content
            if not self.validate_content(content):
                logger.warning(f"Content validation failed for {file_path}")

            return frontmatter, content

        except Exception as e:
            logger.error(f"Error processing markdown file: {str(e)}")
            raise