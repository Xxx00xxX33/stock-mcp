# src/server/infrastructure/connections/baostock_connection.py
"""Async Baostock connection wrapper.

Baostock is a free, open-source Chinese securities data platform.
It requires explicit login/logout for each session.
"""

import asyncio
import logging
from typing import Any, Dict

import baostock as bs

from .base import AsyncDataSourceConnection

logger = logging.getLogger(__name__)


class BaostockConnection(AsyncDataSourceConnection):
    """Async wrapper for Baostock API.
    
    Baostock requires login() before use and logout() after use.
    This connection manages the session lifecycle automatically.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self._login_result = None

    async def connect(self) -> bool:
        """Login to Baostock service.
        
        Baostock allows anonymous login (no credentials needed).
        
        Returns:
            True if login successful, False otherwise
        """
        try:
            loop = asyncio.get_event_loop()
            
            # Baostock login is synchronous, wrap it in executor
            self._login_result = await loop.run_in_executor(None, bs.login)
            
            if self._login_result.error_code == '0':
                self._connected = True
                self._client = bs  # Store the baostock module as client
                logger.info("✅ Baostock connection established (anonymous login)")
                return True
            else:
                logger.error(
                    f"❌ Baostock login failed: {self._login_result.error_msg}"
                )
                self._connected = False
                return False
                
        except Exception as e:
            logger.error(f"❌ Baostock connection error: {e}")
            self._connected = False
            return False

    async def disconnect(self) -> bool:
        """Logout from Baostock service.
        
        Returns:
            True if logout successful, False otherwise
        """
        if not self._connected:
            return True
            
        try:
            loop = asyncio.get_event_loop()
            logout_result = await loop.run_in_executor(None, bs.logout)
            
            self._connected = False
            self._client = None
            self._login_result = None
            
            if logout_result.error_code == '0':
                logger.info("✅ Baostock connection closed")
                return True
            else:
                logger.warning(
                    f"⚠️ Baostock logout warning: {logout_result.error_msg}"
                )
                return True  # Still consider it closed
                
        except Exception as e:
            logger.error(f"❌ Baostock disconnect error: {e}")
            return False

    async def is_healthy(self) -> bool:
        """Check if connection is healthy.
        
        Performs a simple query to verify the connection is working.
        
        Returns:
            True if connection is healthy, False otherwise
        """
        if not self._connected or not self._client:
            return False
            
        try:
            loop = asyncio.get_event_loop()
            
            # Try a simple query: get stock list (limit to 1 row for speed)
            rs = await loop.run_in_executor(
                None,
                lambda: bs.query_all_stock(day="2024-01-01")
            )
            
            if rs.error_code == '0':
                # Just check if we can get data, don't process it
                return True
            else:
                logger.warning(
                    f"⚠️ Baostock health check failed: {rs.error_msg}"
                )
                return False
                
        except Exception as e:
            logger.error(f"❌ Baostock health check exception: {e}")
            return False

    def get_client(self) -> Any:
        """Get the baostock module reference.
        
        Returns:
            The baostock module (bs) if connected, None otherwise
        """
        return self._client
