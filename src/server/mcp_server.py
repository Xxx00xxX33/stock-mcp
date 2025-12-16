"""
基于 FastMCP 的股票数据 MCP 服务器
使用 SSE + HTTP POST 双向通信模式
"""

import builtins
import logging
import sys
import json
from functools import partial

# 导入本地服务
from .services.akshare_service import AkshareService
from .services.fundamentals_service import FundamentalsService
from .services.market_service import MarketDataService
from .services.new_service import get_news_service
from .services.tavily_service import TavilyService
from .services.quote_service import QuoteService
from .services.calendar_service import CalendarService
from .services.macro.macro_service import get_macro_service
from .utils.redis_cache import get_redis_cache
from ..config.settings import get_settings

# 配置日志到stderr
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

# 重定向print到stderr，避免污染MCP的stdout
_original_print = builtins.print
builtins.print = partial(_original_print, file=sys.stderr)

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as e:
    logger.error(f"❌ FastMCP未安装: {e}")
    sys.exit(1)


def clean_dataframe_for_json(df):
    """清理DataFrame中的无效浮点数值，使其符合JSON标准"""
    import pandas as pd
    import numpy as np
    
    if df.empty:
        return []

    try:
        df_cleaned = df.copy()
        df_cleaned = df_cleaned.replace([np.inf, -np.inf], None)
        df_cleaned = df_cleaned.where(pd.notna(df_cleaned), None)
        records = df_cleaned.to_dict("records")

        cleaned_records = []
        for record in records:
            cleaned_record = {}
            for key, value in record.items():
                if value is None:
                    cleaned_record[key] = None
                elif isinstance(value, (int, float)):
                    if np.isnan(value) or np.isinf(value):
                        cleaned_record[key] = None
                    else:
                        cleaned_record[key] = value
                else:
                    cleaned_record[key] = value
            cleaned_records.append(cleaned_record)

        return cleaned_records

    except Exception as e:
        logger.error(f"❌ 清理DataFrame失败: {e}")
        return []


class StockMCPServer:
    """股票数据 MCP 服务器"""

    def __init__(self):
        """初始化服务器和服务"""
        self.settings = get_settings()
        self.redis_cache = get_redis_cache()

        # 初始化服务
        try:
            self.akshare_service = AkshareService()
            logger.info("✅ AkShare服务初始化成功")
        except Exception as e:
            logger.error(f"❌ AkShare服务初始化失败: {e}")
            self.akshare_service = None

        try:
            self.fundamentals_service = FundamentalsService()
            logger.info("✅ 基本面服务初始化成功")
        except Exception as e:
            logger.error(f"❌ 基本面服务初始化失败: {e}")
            self.fundamentals_service = None

        try:
            self.market_service = MarketDataService()
            logger.info("✅ 市场数据服务初始化成功")
        except Exception as e:
            logger.error(f"❌ 市场数据服务初始化失败: {e}")
            self.market_service = None

        try:
            self.news_service = get_news_service(use_proxy=False)
            logger.info("✅ 新闻服务初始化成功")
        except Exception as e:
            logger.error(f"❌ 新闻服务初始化失败: {e}")
            self.news_service = None

        try:
            self.tavily_service = TavilyService(self.settings)
            logger.info("✅ Tavily研究服务初始化成功")
        except Exception as e:
            logger.error(f"❌ Tavily研究服务初始化失败: {e}")
            self.tavily_service = None

        try:
            self.quote_service = QuoteService()
            logger.info("✅ 行情服务初始化成功")
        except Exception as e:
            logger.error(f"❌ 行情服务初始化失败: {e}")
            self.quote_service = None

        try:
            self.calendar_service = CalendarService()
            logger.info("✅ 日历服务初始化成功")
        except Exception as e:
            logger.error(f"❌ 日历服务初始化失败: {e}")
            self.calendar_service = None

        try:
            self.macro_service = get_macro_service()
            logger.info("✅ 宏观数据服务初始化成功")
        except Exception as e:
            logger.error(f"❌ 宏观数据服务初始化失败: {e}")
            self.macro_service = None

    def create_mcp_server(self, port: int = None, host: str = "0.0.0.0") -> FastMCP:
        """创建并配置 FastMCP 服务器

        Args:
            port: 服务器端口
            host: 服务器监听地址，默认 0.0.0.0 允许外部访问
        """
        mcp = FastMCP(
            name="stock-data-server",
            instructions="股票数据分析MCP服务器，提供实时行情、基本面分析、新闻情绪等功能",
            port=port,
            host=host,  # 添加 host 参数
            # 设置为无状态模式，允许独立的JSON-RPC请求（如 tools/list）
            stateless_http=True,
        )

        # 注册工具
        self._register_core_tools(mcp)

        logger.info("🚀 MCP服务器创建完成，已注册所有工具")
        return mcp

    def _register_core_tools(self, mcp: FastMCP):
        """注册核心工具"""

        # ==================== 股票行情工具 ====================

        @mcp.tool()
        async def get_stock_price_data(
            symbol: str, start_date: str, end_date: str
        ) -> str:
            """获取股票价格数据和分析报告

            Args:
                symbol: 股票代码，支持A股(如000001)、港股(如00700)、美股(如AAPL)
                start_date: 开始日期，格式YYYY-MM-DD
                end_date: 结束日期，格式YYYY-MM-DD

            Returns:
                包含股票数据分析的详细报告
            """
            try:
                if self.market_service:
                    report = self.market_service.generate_market_report(
                        symbol, start_date, end_date
                    )
                    return report
                else:
                    return "❌ 市场数据服务当前不可用"

            except Exception as e:
                logger.error(f"获取股票价格数据失败: {e}")
                return f"❌ 获取 {symbol} 股票价格数据失败: {str(e)}"

        @mcp.tool()
        async def get_financial_report(symbol: str) -> str:
            """获取基本面财务报告

            Args:
                symbol: 股票代码

            Returns:
                详细的基本面分析报告，包含估值指标、盈利能力、财务状况等
            """
            try:
                if self.fundamentals_service:
                    report = self.fundamentals_service.generate_fundamental_report(
                        symbol
                    )
                    return report
                else:
                    return "❌ 基本面分析服务当前不可用"

            except Exception as e:
                logger.error(f"获取基本面分析失败: {e}")
                return f"❌ 获取 {symbol} 基本面分析失败: {str(e)}"

        @mcp.tool()
        async def get_latest_news(symbol: str, days_back: int = 30) -> str:
            """获取股票最新新闻

            Args:
                symbol: 股票代码
                days_back: 获取最近几天的新闻，默认30天

            Returns:
                相关新闻列表和情绪分析报告
            """
            try:
                service = self.news_service
                if not service:
                    return "❌ 新闻服务当前不可用"

                result = service.get_news_for_date(symbol, None, days_back)

                if not result.get("success", False):
                    error_msg = result.get("error", "获取新闻失败")
                    return f"❌ 获取 {symbol} 新闻失败: {error_msg}"

                news_list = result.get("news", [])
                if not news_list:
                    return f"📰 {symbol} 最近 {days_back} 天没有找到新闻"

                report = f"# {symbol} 实时新闻分析报告\n\n"
                report += f"📅 时间范围: {result['start_date'][:10]}"
                report += f" 到 {result['end_date'][:10]}\n"
                report += f"📊 新闻总数: {result['total_count']}条\n"
                report += f"🌐 市场: {result['market']}\n\n"

                report += "## 📡 数据源统计\n"
                for source, count in result.get("source_stats", {}).items():
                    report += f"- {source}: {count}条\n"
                report += "\n"

                report += "## 📰 新闻详情\n\n"
                for i, news in enumerate(news_list[:20], 1):
                    report += f"### {i}. {news['title']}\n"
                    report += f"**来源**: {news['source']} | "
                    report += f"**时间**: {news['publish_time'][:19]}\n"
                    if news.get("content"):
                        content = news["content"][:200]
                        report += f"{content}...\n"
                    if news.get("url"):
                        report += f"🔗 [查看原文]({news['url']})\n"
                    report += "\n"

                if len(news_list) > 20:
                    report += f"\n*还有 {len(news_list) - 20} 条新闻未显示*\n"

                return report

            except Exception as e:
                logger.error(f"获取最新新闻失败: {e}")
                return f"❌ 获取 {symbol} 新闻失败: {str(e)}"

        @mcp.tool()
        async def get_news_by_date(
            symbol: str, target_date: str = None, days_before: int = 30
        ) -> str:
            """获取指定日期的股票新闻

            Args:
                symbol: 股票代码
                target_date: 目标日期 (YYYY-MM-DD格式)，默认为当前日期
                days_before: 向前查询的天数，默认30天

            Returns:
                包含新闻数据和元数据的统一响应格式
            """
            try:
                if not self.news_service:
                    return "❌ 新闻服务当前不可用"

                result = self.news_service.get_news_for_date(
                    symbol, target_date, days_before
                )

                if not result.get("success", False):
                    error_msg = result.get("error", "获取新闻失败")
                    return f"❌ 获取 {symbol} 新闻失败: {error_msg}"

                return json.dumps(result, ensure_ascii=False, indent=2)

            except Exception as e:
                logger.error(f"获取指定日期新闻失败: {e}")
                return f"❌ 获取 {symbol} 新闻失败: {str(e)}"

        @mcp.tool()
        async def get_stock_quote(symbol: str) -> str:
            """获取股票的实时或近实时行情数据

            Args:
                symbol: 股票代码

            Returns:
                价格、涨跌幅、市盈率和市值等信息
            """
            try:
                if not self.quote_service:
                    return "❌ 行情服务当前不可用"

                quote_dto = self.quote_service.get_stock_quote(symbol)
                # 将 DTO 对象转换为字典
                if hasattr(quote_dto, '__dict__'):
                    quote_dict = quote_dto.__dict__
                elif hasattr(quote_dto, 'dict'):
                    quote_dict = quote_dto.dict()
                else:
                    quote_dict = dict(quote_dto)
                return json.dumps(quote_dict, ensure_ascii=False, indent=2, default=str)

            except Exception as e:
                logger.error(f"获取股票行情数据失败: {e}")
                return f"❌ 获取 {symbol} 行情数据失败: {str(e)}"

        @mcp.tool()
        async def get_stock_quotes(symbols: list) -> str:
            """批量获取多个股票的实时或近实时行情数据

            Args:
                symbols: 股票代码列表，例如 ["AAPL", "TSLA", "000001"]

            Returns:
                包含多个股票的行情数据
            """
            try:
                if not self.quote_service:
                    return "❌ 行情服务当前不可用"

                if not symbols:
                    return "❌ 股票代码列表不能为空"

                quote_dtos = self.quote_service.get_stock_quotes_batch(symbols)
                # 将 DTO 对象列表转换为字典列表
                quote_dicts = []
                for quote_dto in quote_dtos:
                    if hasattr(quote_dto, '__dict__'):
                        quote_dicts.append(quote_dto.__dict__)
                    elif hasattr(quote_dto, 'dict'):
                        quote_dicts.append(quote_dto.dict())
                    else:
                        quote_dicts.append(dict(quote_dto))
                return json.dumps(quote_dicts, ensure_ascii=False, indent=2, default=str)

            except Exception as e:
                logger.error(f"批量获取股票行情数据失败: {e}")
                return f"❌ 批量获取行情数据失败: {str(e)}"

        # ==================== 日历工具 ====================

        @mcp.tool()
        async def get_trading_days(symbol: str, start_date: str, end_date: str) -> str:
            """获取指定股票的交易日列表

            Args:
                symbol: 股票代码
                start_date: 开始日期，格式YYYY-MM-DD
                end_date: 结束日期，格式YYYY-MM-DD

            Returns:
                交易日列表
            """
            try:
                if not self.calendar_service:
                    return "❌ 日历服务当前不可用"

                result = self.calendar_service.get_trading_days(
                    symbol, start_date, end_date
                )
                return json.dumps(result, ensure_ascii=False, indent=2)

            except Exception as e:
                logger.error(f"获取交易日失败: {e}")
                return f"❌ 获取 {symbol} 交易日失败: {str(e)}"

        @mcp.tool()
        async def check_trading_day(symbol: str, check_date: str) -> str:
            """检查指定日期是否为交易日

            Args:
                symbol: 股票代码
                check_date: 检查日期，格式YYYY-MM-DD

            Returns:
                交易日检查结果
            """
            try:
                if not self.calendar_service:
                    return "❌ 日历服务当前不可用"

                result = self.calendar_service.is_trading_day(symbol, check_date)
                return json.dumps(result, ensure_ascii=False, indent=2)

            except Exception as e:
                logger.error(f"检查交易日失败: {e}")
                return f"❌ 检查 {symbol} 交易日失败: {str(e)}"

        @mcp.tool()
        async def get_trading_hours(symbol: str, check_date: str) -> str:
            """获取指定日期的交易时间信息

            Args:
                symbol: 股票代码
                check_date: 检查日期，格式YYYY-MM-DD

            Returns:
                交易时间信息
            """
            try:
                if not self.calendar_service:
                    return "❌ 日历服务当前不可用"

                result = self.calendar_service.get_trading_hours(symbol, check_date)
                return json.dumps(result, ensure_ascii=False, indent=2)

            except Exception as e:
                logger.error(f"获取交易时间失败: {e}")
                return f"❌ 获取 {symbol} 交易时间失败: {str(e)}"

        @mcp.tool()
        async def get_supported_exchanges() -> str:
            """获取支持的交易所列表

            Returns:
                支持的交易所列表
            """
            try:
                if not self.calendar_service:
                    return "❌ 日历服务当前不可用"

                result = self.calendar_service.get_supported_exchanges()
                return json.dumps(result, ensure_ascii=False, indent=2)

            except Exception as e:
                logger.error(f"获取交易所列表失败: {e}")
                return f"❌ 获取交易所列表失败: {str(e)}"

        # ==================== 宏观经济工具 ====================

        @mcp.tool()
        async def get_macro_dashboard() -> str:
            """获取智能宏观数据仪表板

            自动为不同指标设置最佳的默认期数：
            - GDP: 最近4个季度 (1年)
            - CPI/PPI: 最近12个月 (1年)
            - PMI: 最近12个月 (1年)
            - 货币供应量: 最近12个月 (1年)
            - 社会融资: 最近12个月 (1年)
            - LPR: 最近12期 (通常月度发布)

            Returns:
                包含所有主要宏观指标数据的统一响应
            """
            try:
                if not self.macro_service:
                    return "❌ 宏观数据服务当前不可用"

                dashboard_data = self.macro_service.get_macro_dashboard_data()

                result = {"data": {}, "metadata": dashboard_data["metadata"]}

                for indicator, df in dashboard_data["data"].items():
                    result["data"][indicator] = clean_dataframe_for_json(df)

                return json.dumps(result, ensure_ascii=False, indent=2)

            except Exception as e:
                logger.error(f"获取智能宏观数据仪表板失败: {e}")
                return f"❌ 获取宏观数据仪表板失败: {str(e)}"

        @mcp.tool()
        async def get_gdp_data(
            periods: int = None, start_quarter: str = None, end_quarter: str = None
        ) -> str:
            """获取GDP数据

            Args:
                periods: 获取最近N期数据
                start_quarter: 开始季度，格式如 2024Q1
                end_quarter: 结束季度，格式如 2024Q4

            Returns:
                GDP数据列表
            """
            try:
                if not self.macro_service:
                    return "❌ 宏观数据服务当前不可用"

                data = self.macro_service.get_gdp(
                    periods=periods, start_quarter=start_quarter, end_quarter=end_quarter
                )

                result = clean_dataframe_for_json(data)
                return json.dumps(result, ensure_ascii=False, indent=2)

            except Exception as e:
                logger.error(f"获取GDP数据失败: {e}")
                return f"❌ 获取GDP数据失败: {str(e)}"

        @mcp.tool()
        async def get_cpi_data(
            periods: int = None, start_month: str = None, end_month: str = None
        ) -> str:
            """获取CPI数据

            Args:
                periods: 获取最近N期数据
                start_month: 开始月份，格式如 2024-01
                end_month: 结束月份，格式如 2024-12

            Returns:
                CPI数据列表
            """
            try:
                if not self.macro_service:
                    return "❌ 宏观数据服务当前不可用"

                data = self.macro_service.get_cpi(
                    periods=periods, start_month=start_month, end_month=end_month
                )

                result = clean_dataframe_for_json(data)
                return json.dumps(result, ensure_ascii=False, indent=2)

            except Exception as e:
                logger.error(f"获取CPI数据失败: {e}")
                return f"❌ 获取CPI数据失败: {str(e)}"

        @mcp.tool()
        async def get_ppi_data(
            periods: int = None, start_month: str = None, end_month: str = None
        ) -> str:
            """获取PPI数据

            Args:
                periods: 获取最近N期数据
                start_month: 开始月份，格式如 2024-01
                end_month: 结束月份，格式如 2024-12

            Returns:
                PPI数据列表
            """
            try:
                if not self.macro_service:
                    return "❌ 宏观数据服务当前不可用"

                data = self.macro_service.get_ppi(
                    periods=periods, start_month=start_month, end_month=end_month
                )

                result = clean_dataframe_for_json(data)
                return json.dumps(result, ensure_ascii=False, indent=2)

            except Exception as e:
                logger.error(f"获取PPI数据失败: {e}")
                return f"❌ 获取PPI数据失败: {str(e)}"

        @mcp.tool()
        async def get_pmi_data(
            periods: int = None, start_month: str = None, end_month: str = None
        ) -> str:
            """获取PMI数据

            Args:
                periods: 获取最近N期数据
                start_month: 开始月份，格式如 2024-01
                end_month: 结束月份，格式如 2024-12

            Returns:
                PMI数据列表
            """
            try:
                if not self.macro_service:
                    return "❌ 宏观数据服务当前不可用"

                data = self.macro_service.get_pmi(
                    periods=periods, start_month=start_month, end_month=end_month
                )

                result = clean_dataframe_for_json(data)
                return json.dumps(result, ensure_ascii=False, indent=2)

            except Exception as e:
                logger.error(f"获取PMI数据失败: {e}")
                return f"❌ 获取PMI数据失败: {str(e)}"

        @mcp.tool()
        async def get_money_supply_data(
            periods: int = None, start_month: str = None, end_month: str = None
        ) -> str:
            """获取货币供应量数据

            Args:
                periods: 获取最近N期数据
                start_month: 开始月份，格式如 2024-01
                end_month: 结束月份，格式如 2024-12

            Returns:
                货币供应量数据列表
            """
            try:
                if not self.macro_service:
                    return "❌ 宏观数据服务当前不可用"

                data = self.macro_service.get_money_supply(
                    periods=periods, start_month=start_month, end_month=end_month
                )

                result = clean_dataframe_for_json(data)
                return json.dumps(result, ensure_ascii=False, indent=2)

            except Exception as e:
                logger.error(f"获取货币供应量数据失败: {e}")
                return f"❌ 获取货币供应量数据失败: {str(e)}"

        @mcp.tool()
        async def get_social_financing_data(
            periods: int = None, start_month: str = None, end_month: str = None
        ) -> str:
            """获取社会融资数据

            Args:
                periods: 获取最近N期数据
                start_month: 开始月份，格式如 2024-01
                end_month: 结束月份，格式如 2024-12

            Returns:
                社会融资数据列表
            """
            try:
                if not self.macro_service:
                    return "❌ 宏观数据服务当前不可用"

                data = self.macro_service.get_social_financing(
                    periods=periods, start_month=start_month, end_month=end_month
                )

                result = clean_dataframe_for_json(data)
                return json.dumps(result, ensure_ascii=False, indent=2)

            except Exception as e:
                logger.error(f"获取社会融资数据失败: {e}")
                return f"❌ 获取社会融资数据失败: {str(e)}"

        @mcp.tool()
        async def get_lpr_data(
            periods: int = None, start_date: str = None, end_date: str = None
        ) -> str:
            """获取LPR数据

            Args:
                periods: 获取最近N期数据
                start_date: 开始日期，格式YYYY-MM-DD
                end_date: 结束日期，格式YYYY-MM-DD

            Returns:
                LPR数据列表
            """
            try:
                if not self.macro_service:
                    return "❌ 宏观数据服务当前不可用"

                data = self.macro_service.get_lpr(
                    periods=periods, start_date=start_date, end_date=end_date
                )

                result = clean_dataframe_for_json(data)
                return json.dumps(result, ensure_ascii=False, indent=2)

            except Exception as e:
                logger.error(f"获取LPR数据失败: {e}")
                return f"❌ 获取LPR数据失败: {str(e)}"

        # ==================== 宏观数据组合工具 ====================

        @mcp.tool()
        async def get_economic_cycle_data(start: str, end: str) -> str:
            """获取经济周期相关数据（GDP + PMI + CPI）

            Args:
                start: 开始日期，格式YYYY-MM-DD
                end: 结束日期，格式YYYY-MM-DD

            Returns:
                经济周期相关数据
            """
            try:
                if not self.macro_service:
                    return "❌ 宏观数据服务当前不可用"

                data = self.macro_service.get_economic_cycle_data(start, end)

                result = {}
                for key, df in data.items():
                    result[key] = clean_dataframe_for_json(df)

                return json.dumps(result, ensure_ascii=False, indent=2)

            except Exception as e:
                logger.error(f"获取经济周期数据失败: {e}")
                return f"❌ 获取经济周期数据失败: {str(e)}"

        @mcp.tool()
        async def get_monetary_policy_data(start: str, end: str) -> str:
            """获取货币政策相关数据（货币供应量 + 社融 + LPR）

            Args:
                start: 开始日期，格式YYYY-MM-DD
                end: 结束日期，格式YYYY-MM-DD

            Returns:
                货币政策相关数据
            """
            try:
                if not self.macro_service:
                    return "❌ 宏观数据服务当前不可用"

                data = self.macro_service.get_monetary_policy_data(start, end)

                result = {}
                for key, df in data.items():
                    result[key] = clean_dataframe_for_json(df)

                return json.dumps(result, ensure_ascii=False, indent=2)

            except Exception as e:
                logger.error(f"获取货币政策数据失败: {e}")
                return f"❌ 获取货币政策数据失败: {str(e)}"

        @mcp.tool()
        async def get_inflation_data(start: str, end: str) -> str:
            """获取通胀相关数据（CPI + PPI）

            Args:
                start: 开始日期，格式YYYY-MM-DD
                end: 结束日期，格式YYYY-MM-DD

            Returns:
                通胀相关数据
            """
            try:
                if not self.macro_service:
                    return "❌ 宏观数据服务当前不可用"

                data = self.macro_service.get_inflation_data(start, end)

                result = {}
                for key, df in data.items():
                    result[key] = clean_dataframe_for_json(df)

                return json.dumps(result, ensure_ascii=False, indent=2)

            except Exception as e:
                logger.error(f"获取通胀数据失败: {e}")
                return f"❌ 获取通胀数据失败: {str(e)}"

        @mcp.tool()
        async def get_latest_macro_data(periods: int = 1) -> str:
            """获取所有宏观指标的最新数据

            Args:
                periods: 获取最近N期数据，默认1期

            Returns:
                所有宏观指标的最新数据
            """
            try:
                if not self.macro_service:
                    return "❌ 宏观数据服务当前不可用"

                data = self.macro_service.get_latest_all_indicators(periods=periods)

                result = {}
                has_data = False
                for key, df in data.items():
                    cleaned = clean_dataframe_for_json(df)
                    result[key] = cleaned
                    if cleaned:  # 检查是否有数据
                        has_data = True

                if not has_data:
                    return (
                        "⚠️ 宏观数据库为空，需要先同步数据。\n\n"
                        "请使用 `trigger_macro_sync` 工具触发数据同步，例如：\n"
                        "```\ntrigger_macro_sync(force=True)\n```\n\n"
                        "同步完成后即可查询数据。"
                    )

                return json.dumps(result, ensure_ascii=False, indent=2)

            except Exception as e:
                logger.error(f"获取最新宏观数据失败: {e}")
                return f"❌ 获取最新宏观数据失败: {str(e)}"

        # ==================== 宏观数据同步管理工具 ====================

        @mcp.tool()
        async def trigger_macro_sync(indicator: str = None, force: bool = False) -> str:
            """手动触发宏观数据同步

            Args:
                indicator: 指定要同步的指标，如 'gdp', 'cpi' 等，不指定则同步全部
                force: 是否强制同步，默认False

            Returns:
                同步结果
            """
            try:
                if not self.macro_service:
                    return "❌ 宏观数据服务当前不可用"

                result = self.macro_service.manual_sync(indicator=indicator, force=force)

                return json.dumps(result, ensure_ascii=False, indent=2)

            except Exception as e:
                logger.error(f"触发同步失败: {e}")
                return f"❌ 触发同步失败: {str(e)}"

        @mcp.tool()
        async def get_macro_sync_status() -> str:
            """获取宏观数据同步状态

            Returns:
                同步状态信息
            """
            try:
                if not self.macro_service:
                    return "❌ 宏观数据服务当前不可用"

                status = self.macro_service.get_sync_status()

                return json.dumps(status, ensure_ascii=False, indent=2)

            except Exception as e:
                logger.error(f"获取同步状态失败: {e}")
                return f"❌ 获取同步状态失败: {str(e)}"

        @mcp.tool()
        async def get_macro_service_health() -> str:
            """获取宏观数据服务健康状态

            Returns:
                服务健康状态信息
            """
            try:
                if not self.macro_service:
                    return "❌ 宏观数据服务当前不可用"

                health = self.macro_service.get_service_health()

                return json.dumps(health, ensure_ascii=False, indent=2)

            except Exception as e:
                logger.error(f"获取服务健康状态失败: {e}")
                return f"❌ 获取服务健康状态失败: {str(e)}"

        @mcp.tool()
        async def clear_macro_cache(indicator: str = None) -> str:
            """清除宏观数据缓存

            Args:
                indicator: 指定要清除的指标缓存，不指定则清除全部

            Returns:
                清除结果
            """
            try:
                if not self.macro_service:
                    return "❌ 宏观数据服务当前不可用"

                self.macro_service.clear_cache(indicator=indicator)

                return json.dumps(
                    {"cleared": indicator or "all"},
                    ensure_ascii=False,
                    indent=2
                )

            except Exception as e:
                logger.error(f"清除缓存失败: {e}")
                return f"❌ 清除缓存失败: {str(e)}"

        @mcp.tool()
        async def get_macro_cache_stats() -> str:
            """获取宏观数据缓存统计

            Returns:
                缓存统计信息
            """
            try:
                if not self.macro_service:
                    return "❌ 宏观数据服务当前不可用"

                stats = self.macro_service.get_cache_stats()

                return json.dumps(stats, ensure_ascii=False, indent=2)

            except Exception as e:
                logger.error(f"获取缓存统计失败: {e}")
                return f"❌ 获取缓存统计失败: {str(e)}"

        # ==================== 深度研究工具 ====================

        @mcp.tool()
        async def perform_deep_research(
            topic: str,
            research_type: str = "general",
            symbols: list = None,
        ) -> str:
            """对指定主题或公司进行深入的网络搜索和研究，返回一份总结报告。
            此工具用于探索性分析，与其它获取特定数据的工具形成互补。

            Args:
                topic: 需要研究的核心主题。例如 "半导体行业的最新技术突破" 或 "AI芯片市场前景"。
                research_type: 研究类型。可选值: 'general' (通用), 'company_profile' (公司分析), 'competitor_analysis' (竞品分析), 'industry_analysis' (行业分析)。默认为 'general'。
                symbols: (可选) 相关的股票代码列表。例如 ['NVDA', 'AMD']。当进行公司或竞品分析时，提供此参数可以获得更精确的结果。

            Returns:
                一份Markdown格式的深度研究报告。
            """
            if not self.tavily_service or not self.tavily_service.is_available():
                return "❌ 深度研究服务当前不可用，请检查 TAVILY_API_KEY 配置。"

            try:
                # 1. 构建查询
                query = self._build_query(topic, research_type, symbols)
                logger.info(f"🔬 [深度研究] 类型: {research_type}, 最终查询: '{query}'")

                # 2. 执行搜索
                search_result = self.tavily_service.search(
                    query=query,
                    search_depth="advanced",
                    max_results=7,
                    include_answer=True,
                )

                if not search_result:
                    return f"❌ 未能获取关于 '{query}' 的研究结果。"

                # 3. 格式化报告
                return self._format_research_report(topic, search_result)

            except Exception as e:
                logger.error(f"执行深度研究失败: {e}")
                return f"❌ 执行关于 '{topic}' 的深度研究时发生错误: {str(e)}"

    def _build_query(
        self, topic: str, research_type: str, symbols: list = None
    ) -> str:
        """根据研究类型和参数构建更精确的Tavily查询语句"""
        if not symbols or research_type not in [
            "company_profile",
            "competitor_analysis",
        ]:
            return topic

        # 获取内部基本面数据以丰富查询
        internal_data_summary = []
        if self.fundamentals_service:
            for symbol in symbols:
                try:
                    data = self.fundamentals_service.get_fundamental_data(symbol)
                    summary = (
                        f"{data.company_name}({symbol}): "
                        f"市值 {self.fundamentals_service._format_number(data.market_cap)}元, "
                        f"P/E {data.pe_ratio:.2f}, "
                        f"ROE {data.roe:.2f}%"
                    )
                    internal_data_summary.append(summary)
                except Exception as e:
                    logger.warning(f"获取 {symbol} 内部数据失败: {e}")

        internal_summary_str = "; ".join(internal_data_summary)

        if research_type == "company_profile":
            return (
                f"深入分析公司 {symbols[0]} ({topic}) 的业务模式、核心竞争力、财务状况和未来增长前景。"
                f"已知信息: {internal_summary_str}"
            )
        elif research_type == "competitor_analysis":
            symbol_str = ", ".join(symbols)
            return (
                f"对比分析 {symbol_str} 这几家公司在 '{topic}' 领域的竞争格局、"
                f"各自的优势与劣势、市场份额和未来战略。已知信息: {internal_summary_str}"
            )

        return topic

    def _format_research_report(self, topic: str, search_result: dict) -> str:
        """格式化深度研究报告"""
        report = f"# 深度研究报告: {topic}\n\n"

        if search_result.get("answer"):
            report += f"## 核心摘要 (AI生成)\n\n{search_result['answer']}\n\n"

        if search_result.get("results"):
            report += "## 关键信息来源与摘录\n\n"
            for i, item in enumerate(search_result["results"]):
                report += f"### {i+1}. [{item.get('title', '无标题')}]({item.get('url', '#')})\n"
                report += f"**来源**: {item.get('source', '未知')}\n"
                report += f"> {item.get('content', '无内容')}\n\n---\n\n"

        return report


async def run_mcp_server():
    """运行 MCP 服务器"""
    try:
        server = StockMCPServer()
        mcp = server.create_mcp_server()

        logger.info("🚀 启动股票数据MCP服务器...")
        logger.info(f"服务器名称: {mcp.name}")

        logger.info("✅ 已注册25个工具")

        # 使用正确的 FastMCP 运行方法 (同步函数)
        mcp.run()

    except Exception as e:
        logger.error(f"❌ MCP服务器运行失败: {e}")
        raise


if __name__ == "__main__":
    # 直接运行同步函数，不使用 asyncio.run()
    server = StockMCPServer()
    mcp = server.create_mcp_server()

    logger.info("🚀 启动股票数据MCP服务器...")
    logger.info(f"服务器名称: {mcp.name}")
    logger.info("✅ 已注册25个工具")

    mcp.run()
