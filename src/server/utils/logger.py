# src/server/utils/logger.py
"""Structured logging configuration using structlog.
All modules should import logger via:
    from src.server.utils.logger import logger
"""
import logging
import sys
import structlog


def configure_logging(level: str = "INFO"):
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        stream=sys.stderr,
    )
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
            # 禁用 ASCII 转义以支持 emoji 表情符号的正常显示
            structlog.processors.JSONRenderer(ensure_ascii=False),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


# Initialize at import time
configure_logging()
logger = structlog.get_logger()
