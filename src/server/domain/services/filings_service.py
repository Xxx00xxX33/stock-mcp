# src/server/domain/services/filings_service.py
"""FilingsService – fetches regulatory filings and announcements.
Uses AdapterManager to retrieve data from appropriate sources (Finnhub for SEC, Akshare for A-share).
Returns structured data (JSON).
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from src.server.utils.logger import logger


class FilingsService:
    """Service for retrieving regulatory filings and announcements."""

    def __init__(self, adapter_manager):
        self.adapter_manager = adapter_manager
        self.logger = logger

    async def fetch_periodic_sec_filings(
        self,
        ticker: str,
        forms: Optional[List[str]] = None,
        year: Optional[int] = None,
        quarter: Optional[int] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Fetch SEC periodic filings (10-K/10-Q) with year/quarter.

        Args:
            ticker: US stock ticker
            forms: Filing forms (default: ["10-Q"])
            year: Fiscal year (e.g., 2024)
            quarter: Fiscal quarter (1-4)
            limit: Max results when year is omitted

        Returns:
            List of filing dictionaries
        """
        filing_types = forms or ["10-K", "10-Q", "20-F", "6-K"]

        # Convert year/quarter to date range for adapter
        start_date = None
        end_date = None

        if year:
            # Use year as date range
            start_date = f"{year}-01-01"
            end_date = f"{year}-12-31"

        return await self._fetch_filings(
            ticker, filing_types, start_date, end_date, limit
        )

    async def fetch_event_sec_filings(
        self,
        ticker: str,
        forms: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Fetch SEC event-driven filings (8-K, 3/4/5) with date range.

        Args:
            ticker: US stock ticker
            forms: Filing forms (default: ["8-K"])
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            limit: Max results

        Returns:
            List of filing dictionaries
        """
        filing_types = forms or ["8-K", "6-K"]

        return await self._fetch_filings(
            ticker, filing_types, start_date, end_date, limit
        )

    async def fetch_ashare_filings(
        self,
        symbol: str,
        filing_types: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Fetch A-share announcements.

        Note: Ticker normalization is handled by AkshareAdapter.
        """
        # Delegate to unified method - adapter will handle format
        return await self._fetch_filings(
            symbol, filing_types, start_date, end_date, limit
        )

    async def _fetch_filings(
        self,
        ticker: str,
        filing_types: Optional[List[str]],
        start_date_str: Optional[str],
        end_date_str: Optional[str],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """Internal unified method to fetch filings via AdapterManager."""
        try:
            start = (
                datetime.strptime(start_date_str, "%Y-%m-%d")
                if start_date_str
                else None
            )
            end = datetime.strptime(end_date_str, "%Y-%m-%d") if end_date_str else None

            filings = await self.adapter_manager.get_filings(
                ticker, start, end, limit, filing_types
            )

            return filings

        except Exception as e:
            self.logger.error(f"Failed to fetch filings for {ticker}: {e}")
            return [{"error": str(e)}]
