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

    async def fetch_sec_filings(
        self,
        ticker: str,
        filing_types: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Fetch SEC filings (US stocks)."""
        return await self._fetch_filings(ticker, filing_types, start_date, end_date, limit)

    async def fetch_ashare_filings(
        self,
        symbol: str,
        filing_types: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Fetch A-share announcements."""
        # Ensure ticker format
        if ":" not in symbol:
            # Try to guess or default to SSE/SZSE based on code
            if symbol.startswith("6"):
                ticker = f"SSE:{symbol}"
            elif symbol.startswith(("0", "3")):
                ticker = f"SZSE:{symbol}"
            elif symbol.startswith("8"):
                ticker = f"BSE:{symbol}"
            else:
                ticker = f"SSE:{symbol}" # Default
        else:
            ticker = symbol
            
        return await self._fetch_filings(ticker, filing_types, start_date, end_date, limit)

    async def _fetch_filings(
        self,
        ticker: str,
        filing_types: Optional[List[str]],
        start_date_str: Optional[str],
        end_date_str: Optional[str],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """Internal method to fetch filings via AdapterManager."""
        try:
            start = datetime.strptime(start_date_str, "%Y-%m-%d") if start_date_str else None
            end = datetime.strptime(end_date_str, "%Y-%m-%d") if end_date_str else None
            
            filings = await self.adapter_manager.get_filings(
                ticker, start, end, limit
            )
            
            # Filter by type if needed (client-side filtering as adapters might return all)
            if filing_types:
                filtered = []
                for f in filings:
                    # Check if 'form' or 'type' matches any in filing_types
                    ftype = f.get("form") or f.get("type") or ""
                    if any(t.lower() in ftype.lower() for t in filing_types):
                        filtered.append(f)
                return filtered[:limit]
            
            return filings

        except Exception as e:
            self.logger.error(f"Failed to fetch filings for {ticker}: {e}")
            return [{"error": str(e)}]

    async def get_filing_detail(self, filing_id: str, filing_source: str = "sec") -> Dict[str, Any]:
        """Get detailed content of a filing."""
        # This might require a separate API call or just returning the URL
        # For now, we return a placeholder or the URL if we have it in ID
        return {
            "filing_id": filing_id,
            "source": filing_source,
            "content": "Detail retrieval not yet implemented. Please check the filing URL.",
            "url": filing_id if filing_id.startswith("http") else None
        }

    async def search_filings_by_keyword(
        self,
        keyword: str,
        market: str = "us",
        filing_types: Optional[List[str]] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Search filings by keyword."""
        # This requires a search API which might not be available in standard adapters
        # We can return a not implemented message or try to search news
        return [{"error": "Keyword search for filings not supported by current adapters."}]

    async def get_latest_earnings_reports(
        self, market: str = "us", days: int = 7, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get latest earnings reports."""
        # This requires a calendar API
        return [{"error": "Earnings calendar not supported by current adapters."}]
