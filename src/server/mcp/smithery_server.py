# src/server/mcp/smithery_server.py
"""
Smithery-compatible MCP server entry point.

This module provides a Smithery-compatible server creation function
that wraps the existing FastMCP server with proper decorators and structure.
"""

from fastmcp import FastMCP
from smithery.decorators import smithery
from pydantic import BaseModel, Field
from typing import Optional

from src.server.core.dependencies import Container
from src.server.utils.logger import logger


class ConfigSchema(BaseModel):
    """Configuration schema for the Stock MCP server.
    
    Users can provide these settings when connecting to the server.
    """
    tushare_token: Optional[str] = Field(
        None,
        description="Tushare API token for China A-share data (get from https://tushare.pro/register)"
    )
    finnhub_api_key: Optional[str] = Field(
        None,
        description="Finnhub API key for US stock data (get from https://finnhub.io/)"
    )
    dashscope_api_key: Optional[str] = Field(
        None,
        description="Dashscope API key for AI features (optional)"
    )


@smithery.server(config_schema=ConfigSchema)
def create_server():
    """Create and return a FastMCP server instance for Smithery deployment.
    
    This function is called by Smithery to create the MCP server.
    It initializes all connections, registers adapters, and sets up tools.
    
    Returns:
        FastMCP: Configured MCP server instance
    """
    logger.info("🚀 Creating Stock MCP server for Smithery")
    
    # Create FastMCP instance
    mcp = FastMCP(
        name="stock-tool-mcp",
        version="1.0.0"
    )
    
    # Import tool registration functions
    from src.server.mcp.tools.fundamental_tools import register_fundamental_tools
    from src.server.mcp.tools.news_tools import register_news_tools
    from src.server.mcp.tools.research_tools import register_research_tools
    from src.server.mcp.tools.asset_tools import register_asset_tools
    from src.server.mcp.tools.technical_tools import register_technical_tools
    from src.server.mcp.tools.filings_tools import register_filings_tools
    from src.server.mcp.tools.trade_tools import register_trade_tools
    from src.server.mcp.tools.chunking_tools import register_chunking_tools
    
    # Register all tools
    logger.info("📦 Registering tool groups...")
    
    register_fundamental_tools(mcp)
    logger.info("  ✓ Fundamental tools registered")
    
    register_news_tools(mcp)
    logger.info("  ✓ News tools registered")
    
    register_research_tools(mcp)
    logger.info("  ✓ Research tools registered")
    
    register_asset_tools(mcp)
    logger.info("  ✓ Asset tools registered")
    
    register_technical_tools(mcp)
    logger.info("  ✓ Technical tools registered")
    
    register_filings_tools(mcp)
    logger.info("  ✓ Filings tools registered")
    
    register_trade_tools(mcp)
    logger.info("  ✓ Trade tools registered")
    
    register_chunking_tools(mcp)
    logger.info("  ✓ Chunking tools registered")
    
    logger.info("✅ Stock MCP server created successfully")
    logger.info("📋 Server Information:")
    logger.info(f"   Name: {mcp.name}")
    logger.info(f"   Version: {mcp.version}")
    logger.info("   Protocol: MCP (Model Context Protocol)")
    logger.info("   Transport: Streamable HTTP")
    
    return mcp


async def initialize_connections():
    """Initialize all external connections (Redis, Tushare, etc.).
    
    This function should be called during server startup to establish
    connections to external services.
    """
    logger.info("🔄 Initializing connections...")
    
    # Initialize Redis
    redis = Container.redis()
    await redis.connect()
    logger.info("✅ Redis connection established")
    
    # Initialize Tushare connection
    tushare = Container.tushare()
    tushare_connected = await tushare.connect()
    if tushare_connected:
        logger.info("✅ Tushare connection established")
    else:
        logger.warning("⚠️ Tushare connection failed - will use fallback adapters")
    
    # Initialize FinnHub connection
    finnhub = Container.finnhub()
    await finnhub.connect()
    logger.info("✅ FinnHub connection established")
    
    # Initialize Baostock connection
    baostock = Container.baostock()
    await baostock.connect()
    logger.info("✅ Baostock connection established")


async def register_adapters():
    """Register all data adapters with the adapter manager.
    
    Adapters are registered in priority order:
    - Crypto: CoinGecko > CCXT > Yahoo
    - A-share: Tushare > Akshare > Baostock
    - US stocks: Yahoo > Finnhub
    """
    logger.info("📦 Registering data adapters...")
    adapter_manager = Container.adapter_manager()
    
    # A股数据源 - 按优先级注册
    adapter_manager.register_adapter(Container.tushare_adapter())
    adapter_manager.register_adapter(Container.akshare_adapter())
    adapter_manager.register_adapter(Container.baostock_adapter())
    
    # 加密货币数据源 - 优先级高于 Yahoo（避免被覆盖）
    adapter_manager.register_adapter(Container.crypto_adapter())
    adapter_manager.register_adapter(Container.ccxt_adapter())
    
    # 美股数据源（Yahoo 也支持加密货币，但优先级低）
    adapter_manager.register_adapter(Container.yahoo_adapter())
    adapter_manager.register_adapter(Container.finnhub_adapter())
    
    logger.info("✅ All adapters registered")
    logger.info("   Crypto: CoinGecko > CCXT > Yahoo")
    logger.info("   A-share: Tushare > Akshare > Baostock")
    logger.info("   US stocks: Yahoo > Finnhub")
