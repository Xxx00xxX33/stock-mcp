"""Minimal Smithery-compatible MCP server for testing.

This is a minimal version without any external dependencies to test if Smithery can work.
"""

from fastmcp import FastMCP
from smithery.decorators import smithery
from pydantic import BaseModel, Field
from typing import Optional


class ConfigSchema(BaseModel):
    """Configuration schema for the Stock MCP server."""
    
    tushare_token: Optional[str] = Field(
        default=None,
        description="Tushare API token for Chinese stock market data"
    )


@smithery.server(config_schema=ConfigSchema)
def create_server():
    """Create a minimal FastMCP server for testing.
    
    Returns:
        FastMCP: Configured MCP server instance
    """
    print("🚀 Creating minimal Stock MCP server for Smithery")
    
    # Create FastMCP server
    mcp = FastMCP(
        name="stock-tool-mcp-minimal",
        version="1.0.0"
    )
    
    # Add a simple test tool
    @mcp.tool()
    def test_tool(message: str) -> str:
        """A simple test tool.
        
        Args:
            message: A test message
            
        Returns:
            Echo of the message
        """
        return f"Echo: {message}"
    
    print("✅ Minimal server created successfully")
    
    return mcp
