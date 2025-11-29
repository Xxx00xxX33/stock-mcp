# src/server/api/routes/__init__.py
"""API routes."""

from .market_data import router as market_data_router

__all__ = ["market_data_router"]
