# src/server/mcp/tools/research_tools.py
"""MCP tool for deep research.
Combines market data, fundamental data, and recent news into a structured report.
Returns structured data (JSON).
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict

from fastmcp import FastMCP

from src.server.core.dependencies import Container
from src.server.utils.logger import logger


def register_research_tools(mcp: FastMCP):
    @mcp.tool(tags={"research", "analysis", "core"})
    async def perform_deep_research(symbol: str, days_back: int = 30) -> Dict[str, Any]:
        """Generate a deep research report for `symbol`.

        Aggregates:
        1. Market Data (Price & History)
        2. Fundamental Analysis
        3. Recent News

        Args:
            symbol: Stock symbol
            days_back: News lookback days

        Returns:
            Dictionary containing aggregated research data
        """
        logger.info(
            "MCP tool called: perform_deep_research", symbol=symbol, days_back=days_back
        )

        manager = Container.adapter_manager()
        fundamental_srv = Container.fundamental_service()
        news_srv = Container.news_service()

        # Define tasks
        async def get_market_data():
            try:
                # Get price and recent history
                end = datetime.now()
                start = end - timedelta(days=365)  # 1 year history

                price = await manager.get_real_time_price(symbol)
                history = await manager.get_historical_prices(symbol, start, end)
                info = await manager.get_asset_info(symbol)

                return {
                    "info": info.model_dump(mode="json") if info else None,
                    "price": price.to_dict() if price else None,
                    "history": [p.to_dict() for p in history] if history else [],
                }
            except Exception as e:
                logger.error(f"Market data fetch failed: {e}")
                return {"error": str(e)}

        async def get_fundamentals():
            return await fundamental_srv.get_fundamental_analysis(symbol)

        async def get_news():
            return await news_srv.fetch_latest_news(symbol, days_back)

        # Run concurrently
        market_data, fundamentals, news = await asyncio.gather(
            get_market_data(), get_fundamentals(), get_news()
        )

        return {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "market_data": market_data,
            "fundamentals": fundamentals,
            "news": news,
        }
