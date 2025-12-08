# src/server/core/health.py
"""Health check endpoint for the service.
Returns overall status, connection health, and cache health.
"""

from fastapi import APIRouter
from src.server.core.dependencies import Container
from src.server.utils.logger import logger

router = APIRouter()

@router.get("/health", tags=["Health"])
async def health_check():
    # Get connections from container
    redis_conn = Container.redis()
    # Simple health checks (async) - MySQL disabled
    redis_ok = await redis_conn.is_healthy()
    status = "ok" if redis_ok else "degraded"
    logger.info("Health check executed", redis=redis_ok)
    return {
        "status": status,
        "components": {
            "redis": redis_ok,
            # "mysql": mysql_ok,  # MySQL disabled
        },
    }
