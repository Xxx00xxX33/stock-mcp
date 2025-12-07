from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from src.server.core.dependencies import Container
from src.server.domain.services.filings_service import FilingsService

router = APIRouter(prefix="/filings", tags=["filings"])

# --- Request Models ---

class ProcessDocumentRequest(BaseModel):
    doc_id: str
    url: str
    doc_type: str
    ticker: Optional[str] = None

# --- Endpoints ---

@router.get("/sec/periodic")
async def get_periodic_sec_filings(
    ticker: str = Query(..., description="US stock ticker (e.g., AAPL)"),
    year: Optional[int] = Query(None, description="Fiscal year"),
    quarter: Optional[int] = Query(None, description="Fiscal quarter (1-4)"),
    forms: Optional[List[str]] = Query(None, description="Filing forms (e.g., 10-K, 10-Q)"),
    limit: int = Query(10, description="Max results when year is omitted"),
):
    """Fetch SEC periodic filings (10-K/10-Q)."""
    service: FilingsService = Container.filings_service()
    try:
        return await service.fetch_periodic_sec_filings(
            ticker=ticker,
            forms=forms,
            year=year,
            quarter=quarter,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sec/event")
async def get_event_sec_filings(
    ticker: str = Query(..., description="US stock ticker (e.g., AAPL)"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    forms: Optional[List[str]] = Query(None, description="Filing forms (e.g., 8-K)"),
    limit: int = Query(10, description="Max results"),
):
    """Fetch SEC event-driven filings (8-K, etc.)."""
    service: FilingsService = Container.filings_service()
    try:
        return await service.fetch_event_sec_filings(
            ticker=ticker,
            forms=forms,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ashare")
async def get_ashare_filings(
    symbol: str = Query(..., description="A-share symbol (e.g., 600519)"),
    filing_types: Optional[List[str]] = Query(None, description="Report types (annual, quarterly)"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(10, description="Max results"),
):
    """Fetch A-share announcements."""
    service: FilingsService = Container.filings_service()
    try:
        return await service.fetch_ashare_filings(
            symbol=symbol,
            filing_types=filing_types,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/process")
async def process_document(request: ProcessDocumentRequest):
    """Process a document (download, clean, upload to MinIO)."""
    service: FilingsService = Container.filings_service()
    try:
        result = await service.process_document(
            doc_id=request.doc_id,
            url=request.url,
            doc_type=request.doc_type,
            ticker=request.ticker
        )
        
        if result.get("status") == "failed" or result.get("status") == "error":
             raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))
             
        return result
    except Exception as e:
        # If the service raised an exception directly
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/markdown")
async def get_filing_markdown(
    ticker: str = Query(..., description="Stock ticker (e.g., AAPL or NASDAQ:AAPL)"),
    doc_id: str = Query(..., description="SEC Accession Number (e.g., 0000320193-25-000079)"),
    stream: bool = Query(False, description="If true, return plain text Markdown; otherwise return JSON"),
):
    """Get SEC filing content as Markdown with caching.
    
    This endpoint:
    1. Checks MinIO cache for pre-converted Markdown
    2. If cached, returns immediately (fast path)
    3. If not cached, fetches from SEC, converts to Markdown, caches, and returns
    
    Use `stream=true` for plain text response (suitable for direct file download).
    """
    from fastapi.responses import PlainTextResponse
    
    service: FilingsService = Container.filings_service()
    try:
        result = await service.get_filing_markdown(ticker=ticker, doc_id=doc_id)
        
        if result.get("status") == "error":
            raise HTTPException(
                status_code=404 if "not found" in result.get("error", "").lower() else 500,
                detail=result.get("error", "Unknown error")
            )
        
        # Return plain text if stream=true
        if stream:
            return PlainTextResponse(
                content=result.get("content", ""),
                media_type="text/markdown",
                headers={
                    "X-Cached": str(result.get("cached", False)),
                    "X-Doc-Id": doc_id,
                    "X-Ticker": ticker,
                }
            )
        
        # Default: return JSON with metadata
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

