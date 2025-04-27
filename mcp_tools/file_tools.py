import logging
from mcp.server.fastmcp import FastMCP
from ..content_manager import ContentManager
from ..monitoring import MonitoringManager
from ..exceptions import ContentValidationError, PublishingError

logger = logging.getLogger(__name__)

def register_file_tools(
    mcp: FastMCP,
    content_manager: ContentManager,
    monitoring_manager: MonitoringManager
) -> None:
    """Register file-related tools with the MCP server."""
    
    @mcp.tool(name="read_codebase_file", description="Reads a markdown file from the codebase")
    async def read_codebase_file(file_path: str) -> str:
        """
        Reads a markdown file from the specified path.
        
        Args:
            file_path: Path to the markdown file
            
        Returns:
            File content or error message
        """
        monitoring_manager.record_request("read_codebase_file")
        
        try:
            # Use content_manager to read and process the file
            frontmatter, content = content_manager.process_markdown(file_path, upload_images=False)
            return content
            
        except ContentValidationError as e:
            monitoring_manager.record_error("read_codebase_file", str(type(e).__name__))
            logger.error(f"Content validation error reading file: {str(e)}")
            return f"Content validation error reading file: {str(e)}"
            
        except PublishingError as e:
            monitoring_manager.record_error("read_codebase_file", str(type(e).__name__))
            logger.error(f"Error reading file: {str(e)}")
            return f"Error reading file: {str(e)}"
            
        except Exception as e:
            monitoring_manager.record_error("read_codebase_file", str(type(e).__name__))
            logger.error(f"An unexpected error occurred while reading file: {str(e)}")
            return f"An unexpected error occurred while reading file: {str(e)}" 