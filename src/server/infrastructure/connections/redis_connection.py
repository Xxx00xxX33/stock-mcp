# src/server/infrastructure/connections/redis_connection.py
"""Async Redis connection using redis.asyncio (wrapped via AsyncDataSourceConnection)."""

import asyncio
import logging
from typing import Any, Dict, Optional

import redis.asyncio as aioredis
from .base import AsyncDataSourceConnection

logger = logging.getLogger(__name__)

class RedisConnection(AsyncDataSourceConnection):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self._redis: Optional[aioredis.Redis] = None

    async def connect(self) -> bool:
        try:
            # Build Redis URL
            password = self.config.get('password')
            host = self.config.get('host', 'localhost')
            port = self.config.get('port', 6379)
            db = self.config.get('db', 0)
            
            # Debug log
            logger.info(f"🔍 Redis config: host={host}, port={port}, db={db}, has_password={bool(password)}")
            
            if password:
                redis_url = f"redis://:{password}@{host}:{port}/{db}"
            else:
                redis_url = f"redis://{host}:{port}/{db}"
            
            self._redis = aioredis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=self.config.get('pool_size', 10),
            )
            # health check via PING
            pong = await self._redis.ping()
            self._connected = pong is True
            if self._connected:
                self._client = self._redis
                logger.info("✅ Redis async connection established")
                return True
            else:
                logger.error("❌ Redis ping failed")
                return False
        except Exception as e:
            logger.error(f"❌ Redis connection error: {e}")
            self._connected = False
            return False

    async def disconnect(self) -> bool:
        if self._redis:
            await self._redis.close()
            self._connected = False
            logger.info("✅ Redis connection closed")
            return True
        return False

    async def is_healthy(self) -> bool:
        if not self._redis:
            return False
        try:
            pong = await self._redis.ping()
            healthy = pong is True
            if not healthy:
                logger.warning("⚠️ Redis health check failed")
            return healthy
        except Exception as e:
            logger.error(f"❌ Redis health check exception: {e}")
            return False

    def get_client(self) -> Any:
        return self._redis
