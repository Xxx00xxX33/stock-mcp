import json

# ==========================================
# 更新后的完整原始 JSON 数据
# ==========================================
raw_data_str = """
{"jsonrpc":"2.0","id":"apifox-test-1","result":{"tools":[{"name":"get_financial_report","description":"Get financial report for the given ticker.\\n\\nArgs:\\n    symbol: Stock ticker symbol\\n\\nReturns:\\n    Dictionary containing financial analysis","inputSchema":{"properties":{"symbol":{"type":"string"}},"required":["symbol"],"type":"object"},"outputSchema":{"additionalProperties":true,"type":"object"},"_meta":{"_fastmcp":{"tags":["fundamental-core","fundamental-financial"]}}},{"name":"get_stock_news","description":"Get professional stock news.\\n\\nArgs:\\n    symbol: Stock symbol (e.g. AAPL, 600519)\\n    days_back: Days to look back (default 7)\\n\\nReturns:\\n    Dictionary containing news items","inputSchema":{"properties":{"symbol":{"type":"string"},"days_back":{"default":7,"type":"integer"}},"required":["symbol"],"type":"object"},"outputSchema":{"additionalProperties":true,"type":"object"},"_meta":{"_fastmcp":{"tags":["news-stock"]}}},{"name":"search_news","description":"Flexible news search tool.\\n\\nArgs:\\n    query: Custom search query (required for news_type=\\"general\\")\\n    news_type: Type of news (general, breaking, financial, stock, sector)\\n    ticker: Stock ticker (for financial/stock type)\\n    sector: Industry sector (for financial/sector type)\\n\\nReturns:\\n    List of news items","inputSchema":{"properties":{"query":{"anyOf":[{"type":"string"},{"type":"null"}],"default":null},"news_type":{"default":"general","enum":["general","breaking","financial","stock","sector"],"type":"string"},"ticker":{"anyOf":[{"type":"string"},{"type":"null"}],"default":null},"sector":{"anyOf":[{"type":"string"},{"type":"null"}],"default":null}},"type":"object"},"outputSchema":{"properties":{"result":{"items":{"additionalProperties":true,"type":"object"},"type":"array"}},"required":["result"],"type":"object","x-fastmcp-wrap-result":true},"_meta":{"_fastmcp":{"tags":["news-search"]}}},{"name":"perform_deep_research","description":"Generate a deep research report for `symbol`.\\n\\nAggregates:\\n1. Market Data (Price & History)\\n2. Fundamental Analysis\\n3. Recent News\\n\\nArgs:\\n    symbol: Stock symbol\\n    days_back: News lookback days\\n\\nReturns:\\n    Dictionary containing aggregated research data","inputSchema":{"properties":{"symbol":{"type":"string"},"days_back":{"default":30,"type":"integer"}},"required":["symbol"],"type":"object"},"outputSchema":{"additionalProperties":true,"type":"object"},"_meta":{"_fastmcp":{"tags":["analysis","core","research"]}}},{"name":"search_assets","description":"Search for assets (stocks, ETFs, crypto, etc.).\\n\\nArgs:\\n    query: Search keyword (ticker or name)\\n    asset_types: List of asset types (stock, etf, crypto, index)\\n    limit: Max results (default 10)\\n\\nReturns:\\n    List of asset search results","inputSchema":{"properties":{"query":{"type":"string"},"asset_types":{"default":null,"items":{"type":"string"},"type":"array"},"limit":{"default":10,"type":"integer"}},"required":["query"],"type":"object"},"outputSchema":{"properties":{"result":{"items":{"additionalProperties":true,"type":"object"},"type":"array"}},"required":["result"],"type":"object","x-fastmcp-wrap-result":true},"_meta":{"_fastmcp":{"tags":["asset-extended","asset-search"]}}},{"name":"get_asset_info","description":"Get detailed asset information.\\n\\nArgs:\\n    ticker: Asset ticker (EXCHANGE:SYMBOL)\\n\\nReturns:\\n    Asset details","inputSchema":{"properties":{"ticker":{"type":"string"}},"required":["ticker"],"type":"object"},"outputSchema":{"additionalProperties":true,"type":"object"},"_meta":{"_fastmcp":{"tags":["asset-extended","asset-info"]}}},{"name":"get_real_time_price","description":"Get real-time price for an asset.\\n\\nArgs:\\n    ticker: Asset ticker (EXCHANGE:SYMBOL)\\n\\nReturns:\\n    Real-time price data","inputSchema":{"properties":{"ticker":{"type":"string"}},"required":["ticker"],"type":"object"},"outputSchema":{"additionalProperties":true,"type":"object"},"_meta":{"_fastmcp":{"tags":["asset-extended","asset-price"]}}},{"name":"get_multiple_prices","description":"Get real-time prices for multiple assets.\\n\\nArgs:\\n    tickers: List of asset tickers\\n\\nReturns:\\n    Dictionary mapping tickers to price data","inputSchema":{"properties":{"tickers":{"items":{"type":"string"},"type":"array"}},"required":["tickers"],"type":"object"},"outputSchema":{"additionalProperties":true,"type":"object"},"_meta":{"_fastmcp":{"tags":["asset-extended","asset-price-batch"]}}},{"name":"get_historical_prices","description":"Get historical price data.\\n\\nArgs:\\n    ticker: Asset ticker\\n    start_date: Start date (YYYY-MM-DD)\\n    end_date: End date (YYYY-MM-DD)\\n    interval: Data interval (1d, 1wk, 1mo)\\n\\nReturns:\\n    List of historical price data points","inputSchema":{"properties":{"ticker":{"type":"string"},"start_date":{"type":"string"},"end_date":{"type":"string"},"interval":{"default":"1d","type":"string"}},"required":["ticker","start_date","end_date"],"type":"object"},"outputSchema":{"properties":{"result":{"items":{"additionalProperties":true,"type":"object"},"type":"array"}},"required":["result"],"type":"object","x-fastmcp-wrap-result":true},"_meta":{"_fastmcp":{"tags":["asset-extended","asset-history"]}}},{"name":"get_market_report","description":"Get a comprehensive market report for the given ticker.\\nIncludes current price and asset info.\\n\\nArgs:\\n    symbol: Ticker symbol\\n\\nReturns:\\n    Dictionary with asset info and current price","inputSchema":{"properties":{"symbol":{"type":"string"}},"required":["symbol"],"type":"object"},"outputSchema":{"additionalProperties":true,"type":"object"},"_meta":{"_fastmcp":{"tags":["asset-extended","market-report"]}}},{"name":"calculate_technical_indicators","description":"Calculate technical indicators.\\n\\nSupported indicators:\\n- SMA (20, 50, 200)\\n- EMA (12, 26)\\n- RSI (14)\\n- MACD\\n- Bollinger Bands\\n- KDJ\\n- ATR\\n\\nArgs:\\n    symbol: Stock symbol (e.g., AAPL, 600519)\\n    period: Data period (30d, 90d, 1y)\\n    interval: Data interval (1d)\\n\\nReturns:\\n    Dictionary containing calculated indicators","inputSchema":{"properties":{"symbol":{"type":"string"},"period":{"default":"30d","type":"string"},"interval":{"default":"1d","type":"string"}},"required":["symbol"],"type":"object"},"outputSchema":{"additionalProperties":true,"type":"object"},"_meta":{"_fastmcp":{"tags":["technical-extended","technical-indicators"]}}},{"name":"generate_trading_signal","description":"Generate trading signals based on technical indicators.\\n\\nArgs:\\n    symbol: Stock symbol\\n    period: Analysis period\\n    interval: Data interval\\n\\nReturns:\\n    Dictionary containing trading signals","inputSchema":{"properties":{"symbol":{"type":"string"},"period":{"default":"30d","type":"string"},"interval":{"default":"1d","type":"string"}},"required":["symbol"],"type":"object"},"outputSchema":{"additionalProperties":true,"type":"object"},"_meta":{"_fastmcp":{"tags":["technical-extended","technical-signal"]}}},{"name":"analyze_price_patterns","description":"Analyze price patterns.\\n\\nArgs:\\n    symbol: Stock symbol\\n    period: Analysis period\\n\\nReturns:\\n    Dictionary containing pattern analysis","inputSchema":{"properties":{"symbol":{"type":"string"},"period":{"default":"90d","type":"string"}},"required":["symbol"],"type":"object"},"outputSchema":{"additionalProperties":true,"type":"object"},"_meta":{"_fastmcp":{"tags":["technical-extended","technical-pattern"]}}},{"name":"calculate_support_resistance","description":"Calculate support and resistance levels.\\n\\nArgs:\\n    symbol: Stock symbol\\n    period: Analysis period\\n\\nReturns:\\n    Dictionary containing support/resistance levels","inputSchema":{"properties":{"symbol":{"type":"string"},"period":{"default":"90d","type":"string"}},"required":["symbol"],"type":"object"},"outputSchema":{"additionalProperties":true,"type":"object"},"_meta":{"_fastmcp":{"tags":["technical-extended","technical-support"]}}},{"name":"analyze_volume_profile","description":"Analyze volume profile.\\n\\nArgs:\\n    symbol: Stock symbol\\n    period: Analysis period\\n\\nReturns:\\n    Dictionary containing volume analysis","inputSchema":{"properties":{"symbol":{"type":"string"},"period":{"default":"90d","type":"string"}},"required":["symbol"],"type":"object"},"outputSchema":{"additionalProperties":true,"type":"object"},"_meta":{"_fastmcp":{"tags":["technical-extended","technical-volume"]}}},{"name":"fetch_sec_filings","description":"Get SEC filings (US).\\n\\nArgs:\\n    ticker: US Stock ticker (e.g. AAPL)\\n    filing_types: List of types (10-K, 10-Q, 8-K)\\n    start_date: YYYY-MM-DD\\n    end_date: YYYY-MM-DD\\n    limit: Max results\\n\\nReturns:\\n    List of filings","inputSchema":{"properties":{"ticker":{"type":"string"},"filing_types":{"default":null,"items":{"type":"string"},"type":"array"},"start_date":{"default":null,"type":"string"},"end_date":{"default":null,"type":"string"},"limit":{"default":10,"type":"integer"}},"required":["ticker"],"type":"object"},"outputSchema":{"properties":{"result":{"items":{"additionalProperties":true,"type":"object"},"type":"array"}},"required":["result"],"type":"object","x-fastmcp-wrap-result":true},"_meta":{"_fastmcp":{"tags":["filings-extended","filings-sec"]}}},{"name":"fetch_ashare_filings","description":"Get A-share announcements.\\n\\nArgs:\\n    symbol: A-share code (e.g. 600519)\\n    filing_types: List of types\\n    start_date: YYYY-MM-DD\\n    end_date: YYYY-MM-DD\\n    limit: Max results\\n\\nReturns:\\n    List of announcements","inputSchema":{"properties":{"symbol":{"type":"string"},"filing_types":{"default":null,"items":{"type":"string"},"type":"array"},"start_date":{"default":null,"type":"string"},"end_date":{"default":null,"type":"string"},"limit":{"default":10,"type":"integer"}},"required":["symbol"],"type":"object"},"outputSchema":{"properties":{"result":{"items":{"additionalProperties":true,"type":"object"},"type":"array"}},"required":["result"],"type":"object","x-fastmcp-wrap-result":true},"_meta":{"_fastmcp":{"tags":["filings-ashare","filings-extended"]}}},{"name":"get_filing_detail","description":"Get detailed content of a filing.\\n\\nArgs:\\n    filing_id: Filing ID or URL\\n    filing_source: 'sec' or 'ashare'\\n\\nReturns:\\n    Dictionary with content","inputSchema":{"properties":{"filing_id":{"type":"string"},"filing_source":{"default":"sec","type":"string"}},"required":["filing_id"],"type":"object"},"outputSchema":{"additionalProperties":true,"type":"object"},"_meta":{"_fastmcp":{"tags":["filings-detail","filings-extended"]}}},{"name":"search_filings_by_keyword","description":"Search filings by keyword.\\n\\nArgs:\\n    keyword: Search keyword\\n    market: 'us' or 'china'\\n    filing_types: Filter by types\\n    limit: Max results\\n\\nReturns:\\n    List of filings","inputSchema":{"properties":{"keyword":{"type":"string"},"market":{"default":"us","type":"string"},"filing_types":{"default":null,"items":{"type":"string"},"type":"array"},"limit":{"default":20,"type":"integer"}},"required":["keyword"],"type":"object"},"outputSchema":{"properties":{"result":{"items":{"additionalProperties":true,"type":"object"},"type":"array"}},"required":["result"],"type":"object","x-fastmcp-wrap-result":true},"_meta":{"_fastmcp":{"tags":["filings-extended","filings-search"]}}},{"name":"get_latest_earnings_reports","description":"Get latest earnings reports.\\n\\nArgs:\\n    market: 'us' or 'china'\\n    days: Lookback days\\n    limit: Max results\\n\\nReturns:\\n    List of reports","inputSchema":{"properties":{"market":{"default":"us","type":"string"},"days":{"default":7,"type":"integer"},"limit":{"default":50,"type":"integer"}},"type":"object"},"outputSchema":{"properties":{"result":{"items":{"additionalProperties":true,"type":"object"},"type":"array"}},"required":["result"],"type":"object","x-fastmcp-wrap-result":true},"_meta":{"_fastmcp":{"tags":["filings-earnings","filings-extended"]}}},{"name":"execute_order","description":"Execute a trading order.\\n\\nArgs:\\n    symbol: Trading pair symbol (e.g., \\"BTC/USDT\\", \\"AAPL\\")\\n    side: \\"buy\\" or \\"sell\\"\\n    type: \\"market\\" or \\"limit\\"\\n    quantity: Amount to trade\\n    price: Limit price (required for limit orders)\\n    exchange_id: Optional exchange ID (e.g., \\"binance\\", \\"interactive_brokers\\")\\n\\nReturns:\\n    Order execution result","inputSchema":{"properties":{"symbol":{"type":"string"},"side":{"type":"string"},"type":{"type":"string"},"quantity":{"type":"number"},"price":{"anyOf":[{"type":"number"},{"type":"null"}],"default":null},"exchange_id":{"anyOf":[{"type":"string"},{"type":"null"}],"default":null}},"required":["symbol","side","type","quantity"],"type":"object"},"outputSchema":{"additionalProperties":true,"type":"object"},"_meta":{"_fastmcp":{"tags":["execution","trade"]}}},{"name":"get_account_balance","description":"Get account balance.\\n\\nArgs:\\n    exchange_id: Optional exchange ID\\n\\nReturns:\\n    Account balance information","inputSchema":{"properties":{"exchange_id":{"anyOf":[{"type":"string"},{"type":"null"}],"default":null}},"type":"object"},"outputSchema":{"additionalProperties":true,"type":"object"},"_meta":{"_fastmcp":{"tags":["account","trade"]}}}]}}
"""


def generate_separated_jsonrpc_openapi(json_data):
    try:
        data = json.loads(json_data)
    except json.JSONDecodeError as e:
        print(f"Error: JSON is invalid. {e}")
        return {}

    openapi_spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "MCP Tools (Final)",
            "version": "1.0.0",
            "description": "JSON-RPC 2.0 interface with SSE Header fixes.",
        },
        "servers": [
            {"url": "http://127.0.0.1:9898", "description": "Local RPC Server"}
        ],
        "paths": {},
    }

    tools = data.get("result", {}).get("tools", [])

    for tool in tools:
        name = tool.get("name")
        description = tool.get("description", "")
        tool_args_schema = tool.get("inputSchema", {})
        output_schema = tool.get("outputSchema", {})
        tags = tool.get("_meta", {}).get("_fastmcp", {}).get("tags", ["default"])

        # 1. 构造 JSON-RPC Body
        # 关键：name 固定为工具名，arguments 引用 inputSchema
        rpc_body_schema = {
            "type": "object",
            "properties": {
                "jsonrpc": {"type": "string", "default": "2.0", "example": "2.0"},
                "method": {
                    "type": "string",
                    "default": "tools/call",
                    "example": "tools/call",
                },
                "params": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "default": name, "example": name},
                        "arguments": tool_args_schema,
                    },
                    "required": ["name", "arguments"],
                },
                "id": {
                    "type": "string",
                    "default": "apifox-test-1",
                    "example": "apifox-test-1",
                },
            },
            "required": ["jsonrpc", "method", "params", "id"],
        }

        # 2. 构造路径 (带后缀区分)
        path_key = f"/?_tool={name}"

        operation = {
            "summary": name,
            "description": description,
            "tags": tags,
            "operationId": name,
            # ==========================================
            # Header 参数定义 (解决 406 Not Acceptable)
            # ==========================================
            "parameters": [
                {
                    "name": "Accept",
                    "in": "header",
                    "description": "Required by MCP server (JSON + SSE support)",
                    "required": True,
                    "schema": {
                        "type": "string",
                        "default": "application/json, text/event-stream",
                    },
                    "example": "application/json, text/event-stream",
                }
            ],
            "requestBody": {
                "required": True,
                "content": {"application/json": {"schema": rpc_body_schema}},
            },
            "responses": {
                "200": {
                    "description": "RPC Response",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "jsonrpc": {"type": "string", "example": "2.0"},
                                    "id": {
                                        "type": "string",
                                        "example": "apifox-test-1",
                                    },
                                    "result": output_schema,
                                },
                            }
                        }
                    },
                }
            },
        }

        openapi_spec["paths"][path_key] = {"post": operation}

    return openapi_spec


result = generate_separated_jsonrpc_openapi(raw_data_str)
print(json.dumps(result, indent=2, ensure_ascii=False))
# 如果你想保存到文件，取消下面两行的注释
with open("openapi_mcp.json", "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)
