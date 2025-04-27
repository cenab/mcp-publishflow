from mcp.server.fastmcp import FastMCP
from ..monitoring import MonitoringManager

def register_health_tools(
    mcp: FastMCP,
    monitoring_manager: MonitoringManager
) -> None:
    """Register health-related tools with the MCP server."""
    
    @mcp.tool(name="health_check", description="Check the health status of the service")
    async def health_check() -> dict:
        """
        Returns the health status of the service.
        
        Returns:
            Dictionary containing health status information
        """
        return monitoring_manager.get_health_status() 