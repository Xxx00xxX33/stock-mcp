# AsyncDataSourceConnection – 抽象基类
"""
抽象的异步数据源连接基类，所有具体连接（Redis、MySQL、Tushare、TDX）都继承此类。
实现了统一的 async 接口：connect、disconnect、is_healthy、get_client。
内部使用 `run_in_executor` 包装阻塞 SDK，保持 FastMCP 事件循环不被阻塞。
"""

import abc
import asyncio
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class AsyncDataSourceConnection(abc.ABC):
    """所有外部系统的异步连接基类"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._connected: bool = False
        self._client: Any = None
        self._connection_time = None
        self._error_count = 0

    @abc.abstractmethod
    async def connect(self) -> bool:
        """建立连接，返回 True 表示成功"""

    async def disconnect(self) -> bool:
        """关闭连接，子类可自行实现"""
        try:
            if hasattr(self._client, "close"):
                await asyncio.get_event_loop().run_in_executor(None, self._client.close)
            self._connected = False
            logger.info(f"✅ {self.__class__.__name__} 已断开连接")
            return True
        except Exception as e:
            logger.error(f"❌ {self.__class__.__name__} 断开失败: {e}")
            return False

    async def is_healthy(self) -> bool:
        """默认健康检查，只判断是否已连接，子类可覆盖实现更细粒度检查"""
        return self._connected

    @property
    def connected(self) -> bool:
        return self._connected

    def get_client(self) -> Any:
        """返回底层客户端实例（已建立连接时）"""
        return self._client

    # 简单错误计数帮助做 Failover
    def increment_error(self) -> None:
        self._error_count += 1
        if self._error_count > 3:
            self._connected = False
            logger.warning(f"⚠️ {self.__class__.__name__} 错误次数过多，标记为不健康")

    def reset_error(self) -> None:
        self._error_count = 0
