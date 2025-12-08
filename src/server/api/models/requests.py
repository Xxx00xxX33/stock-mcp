# src/server/api/models/requests.py
"""API request models using Pydantic for validation."""

from pydantic import BaseModel, Field, field_validator
from typing import List


class GetMultiplePricesRequest(BaseModel):
    """批量获取价格请求模型
    
    用于验证批量价格查询的请求参数,确保 ticker 格式正确。
    """
    
    tickers: List[str] = Field(
        ..., 
        description="资产代码列表 (格式: EXCHANGE:SYMBOL)",
        min_length=1,
        max_length=100,
        examples=[["BINANCE:BTCUSDT", "NASDAQ:AAPL", "SSE:600519"]]
    )
    
    @field_validator("tickers")
    @classmethod
    def validate_tickers(cls, v):
        """验证 ticker 格式必须为 EXCHANGE:SYMBOL"""
        for ticker in v:
            if ":" not in ticker:
                raise ValueError(
                    f"Invalid ticker format: '{ticker}'. Expected 'EXCHANGE:SYMBOL' "
                    f"(e.g., 'BINANCE:BTCUSDT', 'NASDAQ:AAPL', 'SSE:600519')"
                )
            parts = ticker.split(":")
            if len(parts) != 2 or not all(part.strip() for part in parts):
                raise ValueError(f"Invalid ticker format: '{ticker}'")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "tickers": ["BINANCE:BTCUSDT", "BINANCE:ETHUSDT", "NASDAQ:AAPL"]
            }
        }


class CalculateTechnicalIndicatorsRequest(BaseModel):
    """计算技术指标请求模型
    
    用于验证技术指标计算的请求参数,包括 symbol、period 和 interval。
    """
    
    symbol: str = Field(
        ..., 
        description="资产代码 (格式: EXCHANGE:SYMBOL)",
        examples=["BINANCE:BTCUSDT", "NASDAQ:AAPL", "SSE:600519"]
    )
    period: str = Field(
        default="30d",
        description="数据周期 (支持格式: 30d, 90d, 1y)",
        pattern=r"^\d+[dmy]$",
        examples=["30d", "90d", "1y"]
    )
    interval: str = Field(
        default="1d",
        description="K线间隔 (支持: 1d=日线, 1h=小时线, 15m=15分钟线)",
        examples=["1d", "1h", "15m", "5m"]
    )
    
    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v):
        """验证 symbol 格式必须为 EXCHANGE:SYMBOL"""
        if ":" not in v:
            raise ValueError(
                f"Invalid symbol format: '{v}'. Expected 'EXCHANGE:SYMBOL' "
                f"(e.g., 'BINANCE:BTCUSDT', 'NASDAQ:AAPL', 'SSE:600519')"
            )
        parts = v.split(":")
        if len(parts) != 2 or not all(part.strip() for part in parts):
            raise ValueError(f"Invalid symbol format: '{v}'")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "BINANCE:BTCUSDT",
                "period": "30d",
                "interval": "1d"
            }
        }
