# src/server/mcp/tools/filings_tools.py
"""MCP tools for SEC and A-share filings.
Provides access to regulatory filings and announcements.
Returns structured data (JSON).
"""

from typing import Any, Dict, List, Optional

from fastmcp import FastMCP

from src.server.core.dependencies import Container
from src.server.utils.logger import logger


def register_filings_tools(mcp: FastMCP):
    """Register filings tools."""

    @mcp.tool(tags={"filings-sec-periodic", "filings-core"})
    async def fetch_periodic_sec_filings(
        ticker: str,
        forms: list[str] = None,
        year: int = None,
        quarter: int = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get SEC periodic filings (10-K/10-Q) for US stocks.

        Designed for regular, scheduled reports with fiscal year/quarter.
        Use this for fundamental analysis and earnings tracking.

        Args:
        Args:
            ticker: US stock ticker (e.g., "AAPL", "TSLA", "BABA")
            forms: Filing types. Defaults to ["10-K", "10-Q", "20-F", "6-K"]
                - "10-K": Annual reports (US companies)
                - "10-Q": Quarterly reports (US companies)
                - "20-F": Annual reports (Foreign Private Issuers, e.g., BABA)
                - "6-K": Current/Quarterly reports (Foreign Private Issuers)
                Example: ["10-K", "10-Q"]
            year: Fiscal year or list of years (e.g., 2024, [2023, 2024])
                When omitted, returns latest filings using `limit`
            quarter: Fiscal quarter (1-4) or list of quarters
                Requires `year` to be provided
                Example: 3 or [1, 3]
            limit: Max results when year is omitted (default: 10)

        Returns:
            List of filing dictionaries with metadata

        Examples:
            # Get AAPL's 2024 annual report
            ticker="AAPL", forms=["10-K"], year=2024

            # Get TSLA's Q3 2024 quarterly report
            ticker="TSLA", forms=["10-Q"], year=2024, quarter=3

            # Get latest 5 quarterly reports
            ticker="MSFT", forms=["10-Q"], limit=5
        """
        try:
            service = Container.filings_service()
            logger.info(
                "MCP tool called: fetch_periodic_sec_filings",
                ticker=ticker,
                forms=forms,
                year=year,
                quarter=quarter,
                limit=limit,
            )

            return await service.fetch_periodic_sec_filings(
                ticker=ticker,
                forms=forms,
                year=year,
                quarter=quarter,
                limit=limit,
            )

        except Exception as e:
            logger.error(f"Fetch periodic SEC filings failed: {e}")
            return [{"error": str(e)}]

    @mcp.tool(tags={"filings-sec-event", "filings-core"})
    async def fetch_event_sec_filings(
        ticker: str,
        forms: list[str] = None,
        start_date: str = None,
        end_date: str = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get SEC event-driven filings (8-K, Forms 3/4/5) for US stocks.

        Designed for irregular, event-triggered reports.
        Use this for news tracking and material event monitoring.

        Args:
        Args:
            ticker: US stock ticker (e.g., "AAPL", "TSLA", "BABA")
            forms: Filing types. Defaults to ["8-K", "6-K"]
                - "8-K": Current reports (US companies)
                - "6-K": Current reports (Foreign Private Issuers, e.g., BABA)
                - "3": Initial insider ownership
                - "4": Changes in insider ownership
                - "5": Annual insider ownership
                Example: ["8-K", "4"]
            start_date: Start date in YYYY-MM-DD format (optional)
            end_date: End date in YYYY-MM-DD format (optional)
            limit: Max results after filtering (default: 10)

        Returns:
            List of filing dictionaries with metadata

        Examples:
            # Get AAPL's latest 8-K filings
            ticker="AAPL", forms=["8-K"], limit=10

            # Get insider trading in past 30 days
            ticker="TSLA", forms=["4"],
            start_date="2024-11-01", end_date="2024-11-30"

            # Get all event filings in a date range
            ticker="MSFT", start_date="2024-10-01",
            end_date="2024-10-31"
        """
        try:
            service = Container.filings_service()
            logger.info(
                "MCP tool called: fetch_event_sec_filings",
                ticker=ticker,
                forms=forms,
                start_date=start_date,
                end_date=end_date,
                limit=limit,
            )

            return await service.fetch_event_sec_filings(
                ticker=ticker,
                forms=forms,
                start_date=start_date,
                end_date=end_date,
                limit=limit,
            )

        except Exception as e:
            logger.error(f"Fetch event SEC filings failed: {e}")
            return [{"error": str(e)}]

    @mcp.tool(tags={"filings-ashare", "filings-extended"})
    async def fetch_ashare_filings(
        symbol: str,
        filing_types: list[str] = None,
        start_date: str = None,
        end_date: str = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get A-share announcements from CNINFO.

        Args:
            symbol: A-share ticker in format EXCHANGE:CODE
                Examples:
                - SSE:600519 (Kweichow Moutai, Shanghai Stock Exchange)
                - SZSE:000001 (Ping An Bank, Shenzhen Stock Exchange)
                - SZSE:300750 (CATL, ChiNext)
                Note: Plain codes like "600519" are also accepted
            filing_types: Report types in ENGLISH ONLY. Supported values:
                - "annual": Annual reports (年报)
                - "semi-annual": Semi-annual reports (半年报/中报)
                - "quarterly": Quarterly reports (季报)
                Example: ["annual", "quarterly"]
                IMPORTANT: Chinese terms like "年报/半年报/季报" are NOT supported
            start_date: Start date in YYYY-MM-DD format (optional)
            end_date: End date in YYYY-MM-DD format (optional)
            limit: Maximum number of results (default: 10)

        Returns:
            List of filing dictionaries with metadata and PDF URLs

        Examples:
            - Get 2024 annual report:
              symbol="SSE:600519", filing_types=["annual"],
              start_date="2024-01-01", end_date="2024-12-31"
            - Get latest quarterly reports:
              symbol="SZSE:300750", filing_types=["quarterly"], limit=5
            - Get all types:
              symbol="SSE:600519", filing_types=None
        """
        try:
            service = Container.filings_service()
            logger.info(
                "MCP tool called: fetch_ashare_filings",
                symbol=symbol,
                types=filing_types,
                limit=limit,
            )

            return await service.fetch_ashare_filings(
                symbol=symbol,
                filing_types=filing_types,
                start_date=start_date,
                end_date=end_date,
                limit=limit,
            )

        except Exception as e:
            logger.error(f"Fetch A-share filings failed: {e}")
            return [{"error": str(e)}]
