# src/server/app.py
"""
Main MCP server application with all tools.

Architecture:
- Single MCP endpoint with all tools organized by tags
- Tools are filtered by tags for different agent types
- Simpler deployment and maintenance
"""
from src.server.mcp.server import create_mcp_server


def create_app():
    """Create the MCP server app.

    Returns:
        Starlette application with MCP protocol support for streamable HTTP.
    """
    # Create the MCP server
    mcp_server = create_mcp_server()

    # Return the streamable HTTP app
    return mcp_server.streamable_http_app(path="/mcp")


# Create the app instance
app = create_app()
