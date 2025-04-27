import logging
from typing import List, Optional
from mcp.server.fastmcp import FastMCP
from ..publishers.medium_publisher import MediumPublisher
from ..content_manager import ContentManager
from ..monitoring import MonitoringManager
from ..exceptions import PublishingError, ContentValidationError, APIError

logger = logging.getLogger(__name__)

def register_medium_tools(
    mcp: FastMCP,
    content_manager: ContentManager,
    monitoring_manager: MonitoringManager,
    medium_publisher: MediumPublisher
) -> None:
    """Register Medium-related tools with the MCP server."""
    
    @mcp.tool(name="publish_to_medium", description="Publishes a post to Medium from a markdown file")
    async def publish_to_medium(
        file_path: str,
        title: str,
        tags: List[str] = None,
        public: bool = True,
        language: Optional[str] = None
    ) -> str:
        """
        Publishes a post to Medium from a markdown file.
        
        Args:
            file_path: Path to the markdown file
            title: Post title
            tags: List of tags for the post
            public: Whether the post is public or draft
            language: Language code (e.g., 'en', 'es', 'fr')
            
        Returns:
            Confirmation message or error
        """
        start_time = time.time()
        monitoring_manager.record_request("publish_to_medium")
        
        try:
            # Process markdown content
            frontmatter, content = content_manager.process_markdown(file_path)
            
            # Use language from frontmatter if not specified
            if not language and 'language' in frontmatter:
                language = frontmatter['language']
            
            # Use tags from frontmatter if not specified
            if not tags and 'tags' in frontmatter:
                tags = frontmatter['tags']
            
            # Publish to Medium
            result = medium_publisher.publish_post(
                title=title,
                content=content,
                tags=tags,
                public=public,
                language=language
            )
            
            monitoring_manager.record_publish_latency("medium", time.time() - start_time)
            logger.info(f"Successfully published to Medium: {title}")
            return result
            
        except (PublishingError, APIError) as e:
            monitoring_manager.record_error("publish_to_medium", str(type(e).__name__))
            logger.error(f"Error publishing to Medium: {str(e)}")
            return f"Error publishing to Medium: {str(e)}"
            
        except Exception as e:
            monitoring_manager.record_error("publish_to_medium", str(type(e).__name__))
            logger.error(f"An unexpected error occurred while publishing to Medium: {str(e)}")
            return f"An unexpected error occurred while publishing to Medium: {str(e)}" 