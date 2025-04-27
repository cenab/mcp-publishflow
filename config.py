import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    """Application settings loaded from environment variables."""
    IMAGE_UPLOAD_URL: str = os.getenv("IMAGE_UPLOAD_URL")
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    REDIS_URL: str = os.getenv("REDIS_URL")
    METRICS_PORT: int = int(os.getenv("METRICS_PORT", "9090"))
    MEDIUM_API_KEY: str = os.getenv("MEDIUM_API_KEY")
    # Default to the potentially incorrect URL for now, will be updated in publishers/medium_publisher.py
    MEDIUM_API_URL: str = os.getenv("MEDIUM_API_URL", "https://api.medium.com/v1/users/me/publications")
    SUBSTACK_API_KEY: str = os.getenv("SUBSTACK_API_KEY")
    DEFAULT_LANGUAGE: str = os.getenv("DEFAULT_LANGUAGE", "en")
    SUPPORTED_LANGUAGES: list[str] = os.getenv("SUPPORTED_LANGUAGES", "en").split(",")
    MIN_CONTENT_LENGTH: int = int(os.getenv("MIN_CONTENT_LENGTH", "50"))
    MAX_TITLE_LENGTH: int = int(os.getenv("MAX_TITLE_LENGTH", "100"))
    MAX_SUBTITLE_LENGTH: int = int(os.getenv("MAX_SUBTITLE_LENGTH", "200"))
    MAX_TAGS: int = int(os.getenv("MAX_TAGS", "5"))

# Create a settings instance
settings = Settings()