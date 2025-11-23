# src/server/infrastructure/connections/tushare_connection.py
"""Async Tushare connection using tushare.pro_api.
Wraps the synchronous Tushare client in an async interface.
"""

import asyncio
import logging
from typing import Any, Dict

import tushare as ts
from .base import AsyncDataSourceConnection

logger = logging.getLogger(__name__)

class TushareConnection(AsyncDataSourceConnection):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self._client: Any = None
        self._token = config.get("token")

    async def connect(self) -> bool:
        try:
            loop = asyncio.get_event_loop()
            self._client = await loop.run_in_executor(
                None, lambda: ts.pro_api(self._token)
            )
            # simple health check: request a tiny piece of data
            df = await loop.run_in_executor(
                None, lambda: self._client.stock_basic(fields="ts_code")
            )
            self._connected = not df.empty
            if self._connected:
                self._client = self._client
                logger.info("✅ Tushare async connection established")
            else:
                logger.error("❌ Tushare health check returned empty data")
            return self._connected
        except Exception as e:
            logger.error(f"❌ Tushare connection error: {e}")
            self._connected = False
            return False

    async def disconnect(self) -> bool:
        # Tushare client does not need explicit close
        self._connected = False
        self._client = None
        logger.info("✅ Tushare connection closed")
        return True

    async def is_healthy(self) -> bool:
        if not self._client:
            return False
        try:
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None, lambda: self._client.stock_basic(fields="ts_code")
            )
            healthy = not df.empty
            if not healthy:
                logger.warning("⚠️ Tushare health check returned empty data")
            return healthy
        except Exception as e:
            logger.error(f"❌ Tushare health check exception: {e}")
            return False

    def get_client(self) -> Any:
        return self._client
