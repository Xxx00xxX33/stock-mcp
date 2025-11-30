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

    def __init__(self, adapter_manager, minio_client=None):
        self.adapter_manager = adapter_manager
        self.minio_client = minio_client
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

    async def process_document(
        self,
        doc_id: str,
        url: str,
        doc_type: str,
    ) -> Dict[str, Any]:
        """Process a single document: download, extract text, and upload to MinIO.
        
        Args:
            doc_id: Unique document identifier
            url: Document URL (SEC HTML or CNINFO PDF)
            doc_type: Document type
            
        Returns:
            Dict with storage_path and status
        """
        if not self.minio_client:
            return {"error": "MinIO client not configured"}

        try:
            import aiohttp
            from bs4 import BeautifulSoup
            
            async with aiohttp.ClientSession() as session:
                # Headers to satisfy SEC requirements
                headers = {
                    "User-Agent": "ValueCell/1.0 (contact@valuecell.ai)",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                }
                
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        return {
                            "doc_id": doc_id,
                            "status": "failed",
                            "error": f"Download failed with status {response.status}"
                        }
                    
                    content_type = response.headers.get("Content-Type", "").lower()
                    content_bytes = await response.read()
                    
                    is_pdf = "pdf" in content_type or url.lower().endswith(".pdf")
                    
                    if is_pdf:
                        # Upload PDF directly
                        object_name = f"raw/{doc_type}/{doc_id}.pdf"
                        storage_path = await self.minio_client.upload_bytes(
                            object_name, 
                            content_bytes, 
                            "application/pdf"
                        )
                        return {
                            "doc_id": doc_id,
                            "type": "pdf",
                            "url": url,
                            "status": "success",
                            "storage_path": storage_path,
                            "message": "PDF uploaded to MinIO."
                        }
                    else:
                        # Assume HTML/Text (SEC Filings) -> Convert to Markdown/Text
                        html = content_bytes.decode('utf-8', errors='ignore')
                        soup = BeautifulSoup(html, "html.parser")
                        
                        # Remove script and style elements
                        for script in soup(["script", "style"]):
                            script.decompose()
                            
                        # Get text
                        text = soup.get_text(separator="\n\n")
                        
                        # Basic cleaning
                        lines = (line.strip() for line in text.splitlines())
                        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                        text = '\n'.join(chunk for chunk in chunks if chunk)
                        
                        # Upload Markdown
                        object_name = f"processed/{doc_type}/{doc_id}.md"
                        storage_path = await self.minio_client.upload_bytes(
                            object_name, 
                            text.encode('utf-8'), 
                            "text/markdown"
                        )
                        
                        return {
                            "doc_id": doc_id,
                            "type": "text",
                            "url": url,
                            "status": "success",
                            "storage_path": storage_path,
                            "message": "Text extracted and uploaded to MinIO."
                        }

        except Exception as e:
            self.logger.error(f"Process document failed for {doc_id}: {e}")
            return {
                "doc_id": doc_id,
                "status": "error",
                "error": str(e)
            }
