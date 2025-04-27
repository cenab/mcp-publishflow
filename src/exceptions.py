"""Custom exception types for the MCP Publish Flow."""

class PublishingError(Exception):
    """Base exception for publishing-related errors."""
    pass

class ContentValidationError(PublishingError):
    """Exception raised for errors in content validation."""
    pass

class AuthenticationError(PublishingError):
    """Exception raised for authentication failures."""
    pass

class RateLimitError(PublishingError):
    """Exception raised when rate limits are exceeded."""
    pass

class APIError(PublishingError):
    """Exception raised for errors during external API calls."""
    def __init__(self, message: str, status_code: int = None, response_text: str = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text