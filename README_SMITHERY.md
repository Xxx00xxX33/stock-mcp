# Stock MCP Server - Smithery 部署版本

这是 Stock MCP Server 的 Smithery 兼容版本，可以直接部署到 [Smithery.ai](https://smithery.ai) 平台。

## 🎯 主要改动

相比原项目，此版本进行了以下改造以支持 Smithery 部署：

### 1. 添加 Smithery 配置文件

- **smithery.yaml**: Smithery 运行时配置
- **pyproject.toml**: Python 项目配置，替代 requirements.txt

### 2. 创建 Smithery 兼容的服务器入口

- **src/server/mcp/smithery_server.py**: 使用 `@smithery.server()` 装饰器的服务器创建函数
- 支持通过 Smithery UI 配置 API 密钥（不再需要 .env 文件）
- 保持所有原有功能和工具不变

### 3. 项目结构调整

```
stock-mcp-smithery/
├── smithery.yaml              # Smithery 配置
├── pyproject.toml             # Python 依赖和配置
├── .env.example               # 本地开发环境变量示例
├── start_smithery.py          # 本地测试启动脚本
├── README_SMITHERY.md         # 本文档
├── src/
│   └── server/
│       ├── mcp/
│       │   ├── smithery_server.py    # Smithery 入口（新增）
│       │   ├── server.py              # 原始服务器（保留）
│       │   └── tools/                 # 所有工具（未修改）
│       ├── domain/                    # 领域层（未修改）
│       ├── infrastructure/            # 基础设施层（未修改）
│       └── ...
└── ...
```

## 🚀 部署到 Smithery

### 方式一：通过 GitHub 部署（推荐）

1. **将代码推送到 GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit for Smithery deployment"
   git remote add origin https://github.com/YOUR_USERNAME/stock-mcp.git
   git push -u origin main
   ```

2. **连接 GitHub 到 Smithery**
   - 访问 [Smithery.ai](https://smithery.ai)
   - 登录并进入 Dashboard
   - 点击 "Connect GitHub"
   - 授权 Smithery 访问你的仓库

3. **部署服务器**
   - 在 Smithery 中选择你的仓库
   - 点击 "Deploy" 按钮
   - Smithery 会自动检测 `smithery.yaml` 并开始构建
   - 等待部署完成（通常需要 2-5 分钟）

4. **配置和使用**
   - 部署成功后，你会获得一个 Smithery URL
   - 用户可以通过 Smithery UI 配置 API 密钥
   - 在 Claude Desktop、Cursor 等 MCP 客户端中添加服务器 URL

### 方式二：使用 Smithery CLI 本地测试

1. **安装依赖**
   ```bash
   # 使用 uv (推荐)
   pip install uv
   uv sync
   
   # 或使用 pip
   pip install -e .
   ```

2. **配置环境变量（本地测试）**
   ```bash
   cp .env.example .env
   # 编辑 .env 填入你的 API 密钥
   ```

3. **启动开发服务器**
   ```bash
   # 使用 Smithery CLI
   uv run dev
   
   # 或启动交互式 playground
   uv run playground
   ```

4. **测试工具**
   - Playground 会在浏览器中打开
   - 你可以测试所有 MCP 工具
   - 查看工具响应和调试问题

## 📋 可用工具

服务器提供以下 22 个工具：

### 基本面分析 (1 个)
- `get_financial_report`: 获取财务报表和健康度评分

### 新闻工具 (1 个)
- `get_latest_news`: 获取最新市场新闻

### 研究工具 (1 个)
- `perform_deep_research`: 深度研究报告（价格+历史+基本面+新闻）

### 资产工具 (6 个)
- `search_assets`: 搜索股票、ETF、加密货币
- `get_asset_info`: 获取资产详细信息
- `get_real_time_price`: 获取实时价格
- `get_multiple_prices`: 批量获取价格
- `get_historical_prices`: 获取历史价格数据
- `get_market_report`: 获取市场报告

### 技术分析 (5 个)
- `calculate_technical_indicators`: 计算技术指标
- `generate_trading_signal`: 生成交易信号
- `analyze_price_patterns`: 分析价格形态
- `detect_support_resistance`: 检测支撑/阻力位
- `calculate_volatility`: 计算波动率

### 公告文件 (5 个)
- `fetch_periodic_sec_filings`: 获取 SEC 定期报告
- `fetch_event_sec_filings`: 获取 SEC 事件报告
- `fetch_ashare_filings`: 获取 A 股公告

### 交易工具 (2 个)
- `execute_order`: 执行交易订单（模拟模式）
- `get_account_balance`: 获取账户余额

### 文档工具 (1 个)
- `get_document_chunks`: 获取文档分块

## 🔧 配置说明

### Smithery UI 配置（生产环境）

当用户连接到你的 Smithery 服务器时，他们可以通过 UI 配置以下参数：

- **tushare_token**: Tushare API 令牌（用于 A 股数据）
- **finnhub_api_key**: Finnhub API 密钥（用于美股数据）
- **dashscope_api_key**: Dashscope API 密钥（可选，用于 AI 功能）

这些配置会通过 `ctx.session_config` 传递给工具，每个用户会话有独立的配置。

### 环境变量配置（本地开发）

本地开发时，可以使用 `.env` 文件配置：

```bash
TUSHARE_TOKEN=your_token
FINNHUB_API_KEY=your_key
DASHSCOPE_API_KEY=your_key
REDIS_HOST=localhost
REDIS_PORT=6379
```

## 🌍 支持的市场

- **美股**: NASDAQ, NYSE（通过 Yahoo Finance, Finnhub）
- **A 股**: 上交所, 深交所（通过 Akshare, Tushare, Baostock）
- **加密货币**: Binance, OKX 等（通过 CCXT, CoinGecko）
- **外汇与指数**: Yahoo Finance

## 📖 使用示例

### 在 Claude Desktop 中使用

1. 获取 Smithery 部署 URL（例如：`https://your-server.smithery.ai`）

2. 编辑 Claude Desktop 配置文件：
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`

3. 添加服务器配置：
   ```json
   {
     "mcpServers": {
       "stock-tools": {
         "url": "https://your-server.smithery.ai"
       }
     }
   }
   ```

4. 重启 Claude Desktop

5. 在对话中使用：
   ```
   请帮我查询贵州茅台（SSE:600519）的实时价格和基本面信息
   ```

### 在 Cursor 中使用

1. 创建 `.cursor/mcp_config.json`：
   ```json
   {
     "mcpServers": {
       "stock-tools": {
         "url": "https://your-server.smithery.ai"
       }
     }
   }
   ```

2. 重启 Cursor

3. 在 AI 对话中使用工具

## 🔍 故障排除

### 部署失败

1. **检查 smithery.yaml**
   - 确保文件存在于项目根目录
   - 确保内容为 `runtime: "python"`

2. **检查 pyproject.toml**
   - 确保 `[tool.smithery]` 配置正确
   - 确保 server 路径指向正确的函数

3. **查看构建日志**
   - 在 Smithery Dashboard 中查看详细错误信息
   - 检查是否有缺失的依赖

### 本地测试失败

1. **检查 Python 版本**
   ```bash
   python --version  # 应该是 3.12+
   ```

2. **检查依赖安装**
   ```bash
   uv sync
   # 或
   pip install -e .
   ```

3. **检查环境变量**
   ```bash
   cat .env  # 确保 API 密钥已配置
   ```

4. **查看日志**
   ```bash
   uv run dev  # 查看启动日志
   ```

### Redis 连接失败

如果本地测试时 Redis 连接失败：

1. **安装 Redis**
   ```bash
   # macOS
   brew install redis
   brew services start redis
   
   # Ubuntu
   sudo apt-get install redis-server
   sudo systemctl start redis
   ```

2. **或者禁用 Redis**
   - 修改 `src/server/mcp/smithery_server.py`
   - 注释掉 Redis 初始化代码

## 📝 与原项目的差异

### 保持不变
- ✅ 所有 22 个工具功能完全相同
- ✅ 数据适配器逻辑未修改
- ✅ 领域层和基础设施层代码未修改
- ✅ 支持的市场和交易所未变

### 新增内容
- ✨ `smithery.yaml` 配置文件
- ✨ `pyproject.toml` 项目配置
- ✨ `smithery_server.py` Smithery 入口
- ✨ `@smithery.server()` 装饰器支持
- ✨ 通过 UI 配置 API 密钥

### 移除内容
- ❌ 不再需要 FastAPI app.py（Smithery 自动处理）
- ❌ 不再需要 uvicorn 启动（Smithery 自动处理）
- ❌ 不再需要手动管理 lifespan（简化为初始化函数）

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 🔗 相关链接

- [Smithery 官方文档](https://smithery.ai/docs)
- [FastMCP 文档](https://github.com/jlowin/fastmcp)
- [MCP 协议规范](https://modelcontextprotocol.io)
- [原项目仓库](https://github.com/Xxx00xxX33/stock-mcp)
