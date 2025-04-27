import logging
from typing import Optional
from mcp.server.fastmcp import FastMCP
from ..publishers.substack_publisher import SubstackPublisher
from ..content_manager import ContentManager
from ..monitoring import MonitoringManager
from ..exceptions import PublishingError, ContentValidationError

logger = logging.getLogger(__name__)

def register_substack_tools(
    mcp: FastMCP,
    content_manager: ContentManager,
    monitoring_manager: MonitoringManager,
    substack_publisher: SubstackPublisher
) -> None:
    """Register Substack-related tools with the MCP server."""
    
    @mcp.tool(name="publish_to_substack", description="Prepares content for manual publishing to Substack")
    async def publish_to_substack(
        file_path: str,
        title: str,
        subtitle: str = "",
        is_paid: bool = False,
        language: Optional[str] = None
    ) -> str:
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
        start_time = time.time()
        monitoring_manager.record_request("publish_to_substack")
        
        try:
            # Process markdown content
            frontmatter, content = content_manager.process_markdown(file_path)
            
            # Use language from frontmatter if not specified
            if not language and 'language' in frontmatter:
                language = frontmatter['language']
            
            # Prepare publishing instructions
            instructions = substack_publisher.prepare_publishing_instructions(
                title=title,
                content=content,
                subtitle=subtitle,
                is_paid=is_paid,
                language=language
            )
            
            monitoring_manager.record_publish_latency("substack", time.time() - start_time)
            return instructions
            
        except ContentValidationError as e:
            monitoring_manager.record_error("publish_to_substack", str(type(e).__name__))
            logger.error(f"Content validation error preparing for Substack: {str(e)}")
            return f"Content validation error preparing for Substack: {str(e)}"
            
        except PublishingError as e:
            monitoring_manager.record_error("publish_to_substack", str(type(e).__name__))
            logger.error(f"Error preparing content for Substack: {str(e)}")
            return f"Error preparing content for Substack: {str(e)}"
            
        except Exception as e:
            monitoring_manager.record_error("publish_to_substack", str(type(e).__name__))
            logger.error(f"An unexpected error occurred while preparing for Substack: {str(e)}")
            return f"An unexpected error occurred while preparing for Substack: {str(e)}"

    @mcp.tool(name="publish_substack_post", description="Publishes content to Substack automatically via browser automation")
    async def publish_substack_post_tool(
        file_path: str,
        title: str,
        subtitle: str = "",
        is_paid: bool = False,
        language: Optional[str] = None
    ) -> str:
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
        start_time = time.time()
        monitoring_manager.record_request("publish_substack_post")

        try:
            # Use the automated publishing method
            result = substack_publisher.publish_automated(
                file_path=file_path,
                title=title,
                subtitle=subtitle,
                is_paid=is_paid,
                language=language
            )

            monitoring_manager.record_publish_latency("substack_automated", time.time() - start_time)
            monitoring_manager.increment_success_count("publish_substack_post")
            return result

        except (ContentValidationError, PublishingError) as e:
            monitoring_manager.record_error("publish_substack_post", str(type(e).__name__))
            monitoring_manager.increment_failure_count("publish_substack_post")
            logger.error(f"Error publishing to Substack automatically: {str(e)}")
            raise PublishingError(f"Failed to publish to Substack automatically: {str(e)}")

        except Exception as e:
            monitoring_manager.record_error("publish_substack_post", str(type(e).__name__))
            monitoring_manager.increment_failure_count("publish_substack_post")
            logger.error(f"An unexpected error occurred while publishing to Substack automatically: {str(e)}")
            raise PublishingError(f"An unexpected error occurred while publishing to Substack automatically: {str(e)}")

    @mcp.tool(name="publish_substack_post", description="Publishes content to Substack automatically via browser automation")
    async def publish_substack_post_tool(
        file_path: str,
        title: str,
        subtitle: str = "",
        is_paid: bool = False,
        language: Optional[str] = None
    ) -> str:
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
        start_time = time.time()
        monitoring_manager.record_request("publish_substack_post")

        try:
            # Use the automated publishing method
            result = substack_publisher.publish_automated(
                file_path=file_path,
                title=title,
                subtitle=subtitle,
                is_paid=is_paid,
                language=language
            )

            monitoring_manager.record_publish_latency("substack_automated", time.time() - start_time)
            monitoring_manager.increment_success_count("publish_substack_post")
            return result

        except (ContentValidationError, PublishingError) as e:
            monitoring_manager.record_error("publish_substack_post", str(type(e).__name__))
            monitoring_manager.increment_failure_count("publish_substack_post")
            logger.error(f"Error publishing to Substack automatically: {str(e)}")
            raise PublishingError(f"Failed to publish to Substack automatically: {str(e)}")

        except Exception as e:
            monitoring_manager.record_error("publish_substack_post", str(type(e).__name__))
            monitoring_manager.increment_failure_count("publish_substack_post")
            logger.error(f"An unexpected error occurred while publishing to Substack automatically: {str(e)}")
            raise PublishingError(f"An unexpected error occurred while publishing to Substack automatically: {str(e)}")

    @mcp.tool(name="publish_substack_post", description="Publishes content to Substack automatically via browser automation")
    async def publish_substack_post_tool(
        file_path: str,
        title: str,
        subtitle: str = "",
        is_paid: bool = False,
        language: Optional[str] = None
    ) -> str:
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
        start_time = time.time()
        monitoring_manager.record_request("publish_substack_post")

        try:
            # Use the automated publishing method
            result = substack_publisher.publish_automated(
                file_path=file_path,
                title=title,
                subtitle=subtitle,
                is_paid=is_paid,
                language=language
            )

            monitoring_manager.record_publish_latency("substack_automated", time.time() - start_time)
            monitoring_manager.increment_success_count("publish_substack_post")
            return result

        except (ContentValidationError, PublishingError) as e:
            monitoring_manager.record_error("publish_substack_post", str(type(e).__name__))
            monitoring_manager.increment_failure_count("publish_substack_post")
            logger.error(f"Error publishing to Substack automatically: {str(e)}")
            raise PublishingError(f"Failed to publish to Substack automatically: {str(e)}")

        except Exception as e:
            monitoring_manager.record_error("publish_substack_post", str(type(e).__name__))
            monitoring_manager.increment_failure_count("publish_substack_post")
            logger.error(f"An unexpected error occurred while publishing to Substack automatically: {str(e)}")
            raise PublishingError(f"An unexpected error occurred while publishing to Substack automatically: {str(e)}")