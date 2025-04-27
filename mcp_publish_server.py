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
    
    substack_publisher = SubstackPublisher()
    
    return medium_publisher, substack_publisher

def register_tools(
    mcp: FastMCP,
    content_manager: ContentManager,
    security_manager: SecurityManager,
    monitoring_manager: MonitoringManager,
    medium_publisher: MediumPublisher,
    substack_publisher: SubstackPublisher
) -> None:
    """Register all tools with the MCP server."""
    # Register Substack tools
    register_substack_tools(
        mcp=mcp,
        content_manager=content_manager,
        monitoring_manager=monitoring_manager,
        substack_publisher=substack_publisher
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
        medium_publisher, substack_publisher = initialize_publishers()
        
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
            substack_publisher=substack_publisher
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