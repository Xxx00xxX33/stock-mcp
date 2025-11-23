"""
Author: weihua hu
Date: 2025-11-21 22:36:52
LastEditTime: 2025-11-22 19:04:47
LastEditors: weihua hu
Description:
"""

# src/server/app.py
"""
Main MCP server application with all tools.

Architecture:
- Single MCP endpoint with all tools organized by tags
- Tools are filtered by tags for different agent types
- Simpler deployment and maintenance
"""
from src.server.mcp.server import create_mcp_server


import os

def create_app():
    """Create the MCP server app.

    Returns:
        Starlette application with MCP protocol support.
        默认使用 stdio 传输，若需要 HTTP 可通过环境变量 MCP_TRANSPORT=streamable-http 覆盖。
    """
    # Create the MCP server
    mcp_server = create_mcp_server()

    # Determine transport (stdio by default)
    transport = os.getenv("MCP_TRANSPORT", "stdio")

    # Return the appropriate app (无状态模式)
    return mcp_server.http_app(
        path="/",
        stateless_http=True,
        transport=transport,
    )


# Create the app instance
app = create_app()

