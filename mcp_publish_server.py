import asyncio
import platform
import logging
from mcp.server.fastmcp import FastMCP

from config import config
from src.content_manager import ContentManager
from src.security import SecurityManager
from src.monitoring import MonitoringManager
from publishers.medium_publisher import MediumPublisher
from publishers.substack_publisher import SubstackPublisher
from publishers.twitter_publisher import TwitterPublisher
from publishers.bluesky_publisher import BlueskyPublisher
from publishers.reddit_publisher import RedditPublisher
from src import exceptions # Assuming exceptions are now in src/exceptions.py

from mcp_tools.substack_tools import register_substack_tools
from mcp_tools.medium_tools import register_medium_tools
from mcp_tools.file_tools import register_file_tools
from mcp_tools.health_tools import register_health_tools

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def initialize_managers():
    """Initialize all manager instances."""
    content_manager = ContentManager(
        image_upload_url=config.IMAGE_UPLOAD_URL
    )
    
    security_manager = SecurityManager(
        secret_key=config.SECRET_KEY,
        redis_url=config.REDIS_URL
    )
    
    monitoring_manager = MonitoringManager(
        metrics_port=config.METRICS_PORT
    )
    
    return content_manager, security_manager, monitoring_manager

def initialize_publishers():
    """Initialize all publisher instances."""
    medium_publisher = MediumPublisher(
        api_key=config.MEDIUM_API_KEY,
        api_url=config.MEDIUM_API_URL
    )
    
    substack_publisher = SubstackPublisher(content_manager=content_manager) # Added content_manager as per SubstackPublisher.__init__
    
    twitter_publisher = TwitterPublisher(
        api_key=config.TWITTER_API_KEY,
        api_secret=config.TWITTER_API_SECRET,
        access_token=config.TWITTER_ACCESS_TOKEN,
        access_token_secret=config.TWITTER_ACCESS_TOKEN_SECRET
    )

    bluesky_publisher = BlueskyPublisher(
        identifier=config.BLUESKY_IDENTIFIER,
        password=config.BLUESKY_PASSWORD
    )

    reddit_publisher = RedditPublisher(
        client_id=config.REDDIT_CLIENT_ID,
        client_secret=config.REDDIT_CLIENT_SECRET,
        username=config.REDDIT_USERNAME,
        password=config.REDDIT_PASSWORD,
        user_agent=config.REDDIT_USER_AGENT
    )
    
    return medium_publisher, substack_publisher, twitter_publisher, bluesky_publisher, reddit_publisher

def register_twitter_tools(
    mcp: FastMCP,
    content_manager: ContentManager,
    monitoring_manager: MonitoringManager,
    twitter_publisher: TwitterPublisher
) -> None:
    """Register Twitter tools with the MCP server."""
    @mcp.tool(name="publish_tweet", description="Publishes a tweet to Twitter")
    async def publish_tweet_tool(file_path: str, medium_link: str, substack_link: str):
        """
        Publishes a tweet based on article content and provided links.

        Args:
            file_path: Path to the markdown file.
            medium_link: URL of the published Medium article.
            substack_link: URL of the published Substack article.
        """
        try:
            frontmatter, _ = content_manager.process_markdown(file_path)
            message = content_manager.generate_social_media_message(frontmatter, medium_link, substack_link)
            result = twitter_publisher.publish_tweet(message)
            monitoring_manager.increment_success_count("publish_tweet")
            return result
        except Exception as e:
            monitoring_manager.increment_failure_count("publish_tweet")
            raise exceptions.PublishingError(f"Failed to publish tweet: {str(e)}")

def register_bluesky_tools(
    mcp: FastMCP,
    content_manager: ContentManager,
    monitoring_manager: MonitoringManager,
    bluesky_publisher: BlueskyPublisher
) -> None:
    """Register Bluesky tools with the MCP server."""
    @mcp.tool(name="publish_bluesky_post", description="Publishes a post to Bluesky")
    async def publish_bluesky_post_tool(file_path: str, medium_link: str, substack_link: str):
        """
        Publishes a Bluesky post based on article content and provided links.

        Args:
            file_path: Path to the markdown file.
            medium_link: URL of the published Medium article.
            substack_link: URL of the published Substack article.
        """
        try:
            frontmatter, _ = content_manager.process_markdown(file_path)
            message = content_manager.generate_social_media_message(frontmatter, medium_link, substack_link)
            result = bluesky_publisher.publish_post(message)
            monitoring_manager.increment_success_count("publish_bluesky_post")
            return result
        except Exception as e:
            monitoring_manager.increment_failure_count("publish_bluesky_post")
            raise exceptions.PublishingError(f"Failed to publish Bluesky post: {str(e)}")

def register_reddit_tools(
    mcp: FastMCP,
    content_manager: ContentManager,
    monitoring_manager: MonitoringManager,
    reddit_publisher: RedditPublisher
) -> None:
    """Register Reddit tools with the MCP server."""
    @mcp.tool(name="find_subreddits", description="Finds relevant subreddits based on article content")
    async def find_subreddits_tool(file_path: str):
        """
        Finds relevant subreddits based on the article's title and tags.

        Args:
            file_path: Path to the markdown file.

        Returns:
            A list of relevant subreddit names.
        """
        try:
            frontmatter, _ = content_manager.process_markdown(file_path)
            keywords = [frontmatter.get('title', '')] + frontmatter.get('tags', [])
            # Filter out empty keywords
            keywords = [keyword for keyword in keywords if keyword]
            relevant_subreddits = reddit_publisher.find_relevant_subreddits(keywords)
            monitoring_manager.increment_success_count("find_subreddits")
            return relevant_subreddits
        except Exception as e:
            monitoring_manager.increment_failure_count("find_subreddits")
            raise exceptions.PublishingError(f"Failed to find subreddits: {str(e)}")

    @mcp.tool(name="publish_reddit_post", description="Publishes a post to a specified subreddit")
    async def publish_reddit_post_tool(file_path: str, subreddit: str, medium_link: str, substack_link: str):
        """
        Publishes a Reddit post based on article content and provided links.

        Args:
            file_path: Path to the markdown file.
            subreddit: The name of the subreddit to post to.
            medium_link: URL of the published Medium article.
            substack_link: URL of the published Substack article.
        """
        try:
            frontmatter, _ = content_manager.process_markdown(file_path)
            title = frontmatter.get('title', 'New Article')
            message = content_manager.generate_social_media_message(frontmatter, medium_link, substack_link)
            result = reddit_publisher.publish_post(subreddit, title, message)
            monitoring_manager.increment_success_count("publish_reddit_post")
            return result
        except Exception as e:
            monitoring_manager.increment_failure_count("publish_reddit_post")
            raise exceptions.PublishingError(f"Failed to publish Reddit post: {str(e)}")


def register_tools(
    mcp: FastMCP,
    content_manager: ContentManager,
    security_manager: SecurityManager,
    monitoring_manager: MonitoringManager,
    medium_publisher: MediumPublisher,
    substack_publisher: SubstackPublisher,
    twitter_publisher: TwitterPublisher,
    bluesky_publisher: BlueskyPublisher,
    reddit_publisher: RedditPublisher
) -> None:
    """Register all tools with the MCP server."""
    # Register Substack tools
    register_substack_tools(
        mcp=mcp,
        content_manager=content_manager,
        monitoring_manager=monitoring_manager,
        substack_publisher=substack_publisher
    )

    # Register Twitter tools
    register_twitter_tools(
        mcp=mcp,
        content_manager=content_manager,
        monitoring_manager=monitoring_manager,
        twitter_publisher=twitter_publisher
    )

    # Register Bluesky tools
    register_bluesky_tools(
        mcp=mcp,
        content_manager=content_manager,
        monitoring_manager=monitoring_manager,
        bluesky_publisher=bluesky_publisher
    )

    # Register Reddit tools
    register_reddit_tools(
        mcp=mcp,
        content_manager=content_manager,
        monitoring_manager=monitoring_manager,
        reddit_publisher=reddit_publisher
    )
    
    # Register Medium tools
    register_medium_tools(
        mcp=mcp,
        content_manager=content_manager,
        monitoring_manager=monitoring_manager,
        medium_publisher=medium_publisher
    )
    
    # Register file tools
    register_file_tools(
        mcp=mcp,
        content_manager=content_manager,
        monitoring_manager=monitoring_manager
    )
    
    # Register health tools
    register_health_tools(
        mcp=mcp,
        monitoring_manager=monitoring_manager
    )

async def main():
    """Main entry point for the MCP server."""
    try:
        # Validate configuration
        config.validate()
        
        # Initialize managers and publishers
        content_manager, security_manager, monitoring_manager = initialize_managers()
        medium_publisher, substack_publisher, twitter_publisher, bluesky_publisher, reddit_publisher = initialize_publishers() # Updated to include new publishers
        
        # Start metrics collection
        monitoring_manager.start_metrics_collection()
        
        # Initialize MCP server
        mcp = FastMCP()
        
        # Register all tools
        register_tools(
            mcp=mcp,
            content_manager=content_manager,
            security_manager=security_manager,
            monitoring_manager=monitoring_manager,
            medium_publisher=medium_publisher,
            substack_publisher=substack_publisher,
            twitter_publisher=twitter_publisher,
            bluesky_publisher=bluesky_publisher,
            reddit_publisher=reddit_publisher
        )
        
        # Run server
        mcp.run(transport='sse')
        
    except Exception as e:
        logger.error(f"Failed to start MCP server: {str(e)}")
        raise

if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())