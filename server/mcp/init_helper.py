# server/mcp/init_helper.py
"""
Initialization helper for Smithery deployment.

Since Smithery doesn't run FastAPI lifespan, we need to initialize
services lazily when they are first accessed.
"""

import asyncio
import functools
from typing import Optional, Callable, Any
from server.core.dependencies import Container
from server.utils.logger import logger

class InitializationHelper:
    """Helper class to manage lazy initialization of services."""
    
    _initialized = False
    _initializing = False
    _init_lock = asyncio.Lock()
    
    @classmethod
    async def ensure_initialized(cls) -> bool:
        """Ensure all services are initialized.
        
        Returns:
            bool: True if initialization succeeded, False otherwise
        """
        if cls._initialized:
            return True
        
        async with cls._init_lock:
            # Double-check after acquiring lock
            if cls._initialized:
                return True
            
            if cls._initializing:
                # Already initializing in another coroutine
                return False
            
            cls._initializing = True
            
            try:
                logger.info("🔄 Initializing services for Smithery deployment...")
                
                # Initialize Redis (optional, use in-memory cache if fails)
                try:
                    redis = Container.redis()
                    await redis.connect()
                    logger.info("✅ Redis connection established")
                except Exception as e:
                    logger.warning(f"⚠️ Redis connection failed: {e}, using in-memory cache")
                
                # Initialize Tushare connection (optional)
                try:
                    tushare = Container.tushare()
                    tushare_connected = await tushare.connect()
                    if tushare_connected:
                        logger.info("✅ Tushare connection established")
                    else:
                        logger.warning("⚠️ Tushare connection failed - will use fallback adapters")
                except Exception as e:
                    logger.warning(f"⚠️ Tushare initialization failed: {e}")
                
                # Initialize FinnHub connection (optional)
                try:
                    finnhub = Container.finnhub()
                    await finnhub.connect()
                    logger.info("✅ FinnHub connection established")
                except Exception as e:
                    logger.warning(f"⚠️ FinnHub initialization failed: {e}")
                
                # Initialize Baostock connection (optional)
                try:
                    baostock = Container.baostock()
                    await baostock.connect()
                    logger.info("✅ Baostock connection established")
                except Exception as e:
                    logger.warning(f"⚠️ Baostock initialization failed: {e}")
                
                # Register adapters
                logger.info("📦 Registering data adapters...")
                adapter_manager = Container.adapter_manager()
                
                # A股数据源 - 按优先级注册
                try:
                    adapter_manager.register_adapter(Container.tushare_adapter())
                    adapter_manager.register_adapter(Container.akshare_adapter())
                    adapter_manager.register_adapter(Container.baostock_adapter())
                except Exception as e:
                    logger.warning(f"⚠️ Failed to register A-share adapters: {e}")
                
                # 加密货币数据源
                try:
                    adapter_manager.register_adapter(Container.crypto_adapter())
                    adapter_manager.register_adapter(Container.ccxt_adapter())
                except Exception as e:
                    logger.warning(f"⚠️ Failed to register crypto adapters: {e}")
                
                # 美股数据源
                try:
                    adapter_manager.register_adapter(Container.yahoo_adapter())
                    adapter_manager.register_adapter(Container.finnhub_adapter())
                except Exception as e:
                    logger.warning(f"⚠️ Failed to register US stock adapters: {e}")
                
                logger.info("✅ All adapters registered")
                logger.info("   Crypto: CoinGecko > CCXT > Yahoo")
                logger.info("   A-share: Tushare > Akshare > Baostock")
                logger.info("   US stocks: Yahoo > Finnhub")
                
                cls._initialized = True
                cls._initializing = False
                
                logger.info("✅ Services initialized successfully")
                return True
                
            except Exception as e:
                logger.error(f"❌ Service initialization failed: {e}", exc_info=True)
                cls._initializing = False
                return False
    
    @classmethod
    def reset(cls):
        """Reset initialization state (for testing)."""
        cls._initialized = False
        cls._initializing = False


def ensure_initialized(func: Callable) -> Callable:
    """Decorator to ensure services are initialized before tool execution.
    
    Usage:
        @mcp.tool()
        @ensure_initialized
        async def my_tool(...):
            ...
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        await InitializationHelper.ensure_initialized()
        return await func(*args, **kwargs)
    return wrapper
