#!/usr/bin/env python3
"""
Local startup script for testing the Smithery-compatible MCP server.

This script initializes connections and starts the server in a way
that mimics how Smithery will run it in production.
"""

import asyncio
from src.server.mcp.smithery_server import (
    create_server,
    initialize_connections,
    register_adapters
)
from src.server.utils.logger import logger


async def startup():
    """Perform startup initialization."""
    try:
        # Initialize connections
        await initialize_connections()
        
        # Register adapters
        await register_adapters()
        
        logger.info("✅ Startup complete")
    except Exception as e:
        logger.error(f"Startup failed: {e}", exc_info=True)
        raise


async def main():
    """Main entry point for local testing."""
    logger.info("=" * 70)
    logger.info("🚀 Starting Stock MCP Server (Smithery Mode)")
    logger.info("=" * 70)
    
    # Perform startup
    await startup()
    
    # Create server
    mcp = create_server()
    
    logger.info("\n" + "=" * 70)
    logger.info("✅ Server ready!")
    logger.info("=" * 70)
    logger.info("\nTo run with Smithery CLI:")
    logger.info("  uv run dev")
    logger.info("  uv run playground")
    logger.info("\nTo deploy to Smithery:")
    logger.info("  1. Push code to GitHub")
    logger.info("  2. Connect GitHub to Smithery")
    logger.info("  3. Click Deploy in Deployments tab")
    logger.info("=" * 70 + "\n")
    
    # Run the server
    # Note: In production, Smithery handles the server lifecycle
    # This is just for local testing
    mcp.run()


if __name__ == "__main__":
    asyncio.run(main())
