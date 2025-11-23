# ValueCell 混合架构重构设计文档

**版本**: 2.0
**日期**: 2025-11-23
**状态**: 待评审
**核心理念**: Java (大脑/状态/业务) + Python (感知/计算/执行)

---

## 1. 整体架构设计 (System Architecture)

### 1.1 架构概述
本方案采用 **多语言微服务架构 (Polyglot Microservices)**。
*   **Java 端 (Spring AI Alibaba)**: 作为系统的核心控制塔。负责策略的生命周期管理、状态持久化、Agent 编排与决策、定时任务调度以及用户接口。
*   **Python 端 (MCP Server)**: 作为系统的基础设施与工具层。负责连接外部金融数据源、执行复杂的数学/技术指标计算、以及作为执行网关（如对接交易所 API）。

### 1.2 架构图 (Mermaid)

```mermaid
graph TD
    User[用户/前端] -->|REST API| JavaGateway[Java API Gateway]
    
    subgraph "Java Core (Spring AI Alibaba)"
        JavaGateway --> StrategyMgr[策略管理服务]
        Scheduler[任务调度器] -->|Trigger| StrategyMgr
        
        StrategyMgr --> AgentCore[Agent 核心编排]
        AgentCore -->|Prompt| LLM[大模型 (Qwen/DeepSeek)]
        
        AgentCore -->|State Read/Write| DB[(MySQL 数据库)]
        
        AgentCore -->|MCP Client| MCPClient[MCP 客户端]
    end
    
    subgraph "Python Infrastructure (MCP Server)"
        MCPClient -->|JSON-RPC| PythonServer[Stock Tool MCP]
        
        PythonServer -->|Pandas/TA-Lib| CalcEngine[计算引擎]
        PythonServer -->|CCXT/SDK| ExecutionGateway[交易执行网关]
        
        PythonServer -->|HTTP| DataSources[数据源 (Tushare/Akshare/Yahoo)]
    end
```

### 1.3 核心职责划分

| 功能模块 | 负责端 | 关键技术栈 | 说明 |
| :--- | :--- | :--- | :--- |
| **策略管理** | **Java** | Spring Boot, JPA | 策略的增删改查、启动停止 |
| **状态持久化** | **Java** | MySQL | 资金、持仓、交易记录的唯一真理来源 |
| **任务调度** | **Java** | Spring Scheduled / Quartz | 决定何时触发策略运行 (如每15分钟) |
| **智能决策** | **Java** | Spring AI Alibaba | 组装 Context，调用 LLM，解析结果 |
| **数据获取** | **Python** | Akshare, Tushare, YFinance | 屏蔽不同数据源的差异，统一格式 |
| **指标计算** | **Python** | Pandas, TA-Lib | 处理 MACD, RSI, 布林带等复杂计算 |
| **实盘交易** | **Python** | CCXT, Playwright | (可选) 如果需要实盘，Python SDK 更丰富 |

---

## 2. 数据库设计 (Database Schema)

所有业务数据均存储在 Java 端连接的 MySQL 中。

### 2.1 策略配置表 (`t_strategy`)
```sql
CREATE TABLE t_strategy (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '物理主键',
    biz_id VARCHAR(64) NOT NULL UNIQUE COMMENT '业务ID (UUID)',
    user_id VARCHAR(64) NOT NULL COMMENT '用户ID',
    name VARCHAR(100) NOT NULL COMMENT '策略名称',
    status VARCHAR(20) NOT NULL DEFAULT 'STOPPED' COMMENT '状态: RUNNING, STOPPED, PAUSED, ERROR',
    
    -- 核心配置
    initial_capital DECIMAL(20, 8) NOT NULL COMMENT '初始资金',
    base_currency VARCHAR(10) DEFAULT 'USD' COMMENT '本位币',
    symbols TEXT COMMENT '标的列表 (JSON Array): ["BTC-USD", "ETH-USD"]',
    interval_period VARCHAR(10) DEFAULT '1h' COMMENT '执行周期: 15m, 1h, 4h',
    
    -- 运行时元数据
    agent_model VARCHAR(64) COMMENT '使用的模型: qwen-max, deepseek-v3',
    risk_level VARCHAR(20) DEFAULT 'MEDIUM' COMMENT '风险偏好',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user (user_id)
) COMMENT '策略实例配置表';
```

### 2.2 策略持仓快照表 (`t_strategy_holding`)
用于记录每次决策后的持仓状态，形成时间序列数据。
```sql
CREATE TABLE t_strategy_holding (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    strategy_biz_id VARCHAR(64) NOT NULL COMMENT '关联策略ID',
    snapshot_time DATETIME NOT NULL COMMENT '快照时间',
    
    symbol VARCHAR(32) NOT NULL COMMENT '标的代码',
    direction VARCHAR(10) NOT NULL COMMENT '方向: LONG, SHORT',
    quantity DECIMAL(20, 8) NOT NULL COMMENT '持仓数量',
    avg_entry_price DECIMAL(20, 8) COMMENT '平均持仓成本',
    
    -- 动态数据 (来自 Python 查询时的最新价)
    last_price DECIMAL(20, 8) COMMENT '快照时的市价',
    unrealized_pnl DECIMAL(20, 8) COMMENT '未实现盈亏',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_strategy_time (strategy_biz_id, snapshot_time)
) COMMENT '策略持仓快照表';
```

### 2.3 策略资产净值表 (`t_strategy_portfolio`)
记录账户整体的资金曲线。
```sql
CREATE TABLE t_strategy_portfolio (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    strategy_biz_id VARCHAR(64) NOT NULL,
    snapshot_time DATETIME NOT NULL,
    
    total_equity DECIMAL(20, 8) NOT NULL COMMENT '总权益 (现金 + 持仓市值)',
    available_cash DECIMAL(20, 8) NOT NULL COMMENT '可用现金',
    frozen_cash DECIMAL(20, 8) DEFAULT 0 COMMENT '冻结资金',
    total_pnl DECIMAL(20, 8) COMMENT '累计盈亏',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_strategy_time (strategy_biz_id, snapshot_time)
) COMMENT '策略资产净值表';
```

### 2.4 交易执行记录表 (`t_strategy_trade`)
记录每一次 AI 做出的交易决策。
```sql
CREATE TABLE t_strategy_trade (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    trade_biz_id VARCHAR(64) NOT NULL UNIQUE COMMENT '交易流水号',
    strategy_biz_id VARCHAR(64) NOT NULL,
    
    symbol VARCHAR(32) NOT NULL,
    action VARCHAR(10) NOT NULL COMMENT 'BUY, SELL',
    trade_type VARCHAR(10) NOT NULL COMMENT 'LONG, SHORT',
    
    price DECIMAL(20, 8) NOT NULL COMMENT '成交/委托价格',
    quantity DECIMAL(20, 8) NOT NULL COMMENT '数量',
    total_amount DECIMAL(20, 8) NOT NULL COMMENT '成交总额',
    fee DECIMAL(20, 8) DEFAULT 0 COMMENT '手续费',
    
    trade_time DATETIME NOT NULL COMMENT '交易时间',
    
    -- AI 思考过程
    reasoning TEXT COMMENT 'AI 决策理由',
    ai_confidence DECIMAL(5, 2) COMMENT 'AI 置信度 (0-100)',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_strategy (strategy_biz_id)
) COMMENT '策略交易记录表';
```

---

## 3. 接口与数据结构设计 (Protocol Design)

### 3.1 Python MCP Tools 定义
Python 端通过 `@mcp.tool` 暴露以下标准接口供 Java 调用。

#### Tool 1: `get_market_technical_analysis`
*   **描述**: 获取指定标的的技术面分析数据。
*   **输入 (Input)**:
    ```json
    {
      "symbol": "BTC-USD",
      "interval": "1h",
      "indicators": ["MACD", "RSI", "BOLL", "EMA"]
    }
    ```
*   **输出 (Output)**:
    ```json
    {
      "symbol": "BTC-USD",
      "timestamp": "2025-11-23T10:00:00Z",
      "current_price": 98500.50,
      "volume_24h": 1500000000,
      "indicators": {
        "macd": {"diff": 120.5, "dea": 100.2, "hist": 20.3, "trend": "BULLISH"},
        "rsi": {"value": 65.4, "status": "NEUTRAL"},
        "boll": {"upper": 99000, "middle": 97000, "lower": 95000, "status": "WITHIN_BAND"}
      }
    }
    ```

#### Tool 2: `get_assets_snapshot` (批量)
*   **描述**: 批量获取一组标的的最新价格，用于 Java 端计算持仓市值。
*   **输入**: `{"symbols": ["BTC-USD", "ETH-USD"]}`
*   **输出**: `{"BTC-USD": 98500.0, "ETH-USD": 3400.0}`

#### Tool 3: `execute_market_order` (可选，实盘用)
*   **描述**: 发送实盘交易指令。
*   **输入**: `{"symbol": "...", "side": "BUY", "quantity": 0.1}`
*   **输出**: `{"order_id": "...", "status": "FILLED", "avg_price": ...}`

### 3.2 Java 内部领域对象 (Domain Objects)

#### `StrategyContext`
用于传递给 LLM 的上下文对象。
```java
public class StrategyContext {
    // 静态配置
    private String strategyName;
    private String riskProfile;
    
    // 动态状态 (来自 DB)
    private BigDecimal availableCash;
    private List<PositionSummary> currentPositions;
    
    // 市场感知 (来自 Python Tool)
    private MarketAnalysisData marketData;
}
```

#### `AgentDecision`
LLM 返回的决策结构（通过 Structured Output Parser 解析）。
```java
public record AgentDecision(
    String action,      // BUY, SELL, HOLD
    String symbol,
    BigDecimal quantity,
    String reasoning,   // 思考过程
    Double confidence   // 置信度
) {}
```

---

## 4. Java 端系统设计 (Brain)

### 4.1 核心服务: `StrategyDomainService`
*   **`runStrategyCycle(Long strategyId)`**: 核心驱动方法。
    1.  **Load**: 从 DB 加载策略配置和当前持仓。
    2.  **Sense**: 调用 MCP Client (`get_market_technical_analysis`) 获取数据。
    3.  **Update State**: 根据最新价格更新持仓的浮动盈亏 (Mark-to-Market)。
    4.  **Think**: 
        *   构建 Prompt (包含 System Prompt + Context)。
        *   调用 `ChatClient` (Spring AI)。
    5.  **Decide**: 解析 LLM 返回的 JSON。
    6.  **Act**: 
        *   如果是 Paper Trading: 直接更新 DB 中的资金和持仓表。
        *   如果是 Live Trading: 调用 MCP Tool (`execute_market_order`)，根据返回结果更新 DB。
    7.  **Persist**: 保存 `t_strategy_trade` 和 `t_strategy_portfolio`。

### 4.2 调度模块
*   使用 Spring `@Scheduled` 或 Quartz。
*   扫描 `t_strategy` 表中 `status = 'RUNNING'` 的策略。
*   根据 `interval_period` 判断是否到达执行时间点。

---

## 5. Python 端系统设计 (Hands)

### 5.1 适配器层 (`adapters/`)
*   **保持现状**: 继续使用现有的 `AdapterManager` 架构。
*   **增强**: 确保 `get_historical_prices` 和 `get_current_price` 对所有数据源（A股/美股/Crypto）都能稳定返回。

### 5.2 计算层 (`services/technical_service.py`)
*   **纯函数式设计**: 输入 DataFrame，输出指标 Dict。
*   **库**: 强依赖 `pandas`, `ta-lib` (或 `pandas-ta`)。
*   **职责**: 
    *   计算移动平均线 (SMA/EMA)。
    *   计算动量指标 (RSI, MACD)。
    *   计算波动率指标 (ATR, Bollinger Bands)。
    *   **关键**: 将复杂的数学计算封装在这里，不要让 Java 做数学题。

### 5.3 MCP 工具层 (`mcp/tools/`)
*   **清理**: 移除所有与 `Agent`、`Conversation`、`User` 相关的代码。
*   **专注**: 只保留 `Market`, `Technical`, `Asset` 相关的 Tools。
*   **格式化**: 确保所有 Tool 返回的都是标准的 JSON 格式，方便 Java Jackson 库解析。

---

## 6. 迁移路线图 (Migration Roadmap)

1.  **Phase 1: Python 瘦身**
    *   在 Python 项目中，标记并废弃 `agents/` 目录。
    *   完善 `technical_tools.py`，确保能返回 Java 所需的所有指标数据。
    *   验证 Python MCP Server 的独立运行能力。

2.  **Phase 2: Java 基础设施搭建**
    *   创建 Spring Boot 项目 (或在现有项目中新增模块)。
    *   集成 `spring-ai-alibaba-starter`。
    *   创建上述 MySQL 表结构。
    *   生成 POJO 和 Repository 代码。

3.  **Phase 3: 核心逻辑迁移**
    *   在 Java 中实现 `StrategyDomainService`。
    *   实现 MCP Client 调用 Python 接口。
    *   调试 "Java 触发 -> Python 获取数据 -> Java LLM 决策 -> Java 落库" 的全链路。

4.  **Phase 4: 完善与测试**
    *   实现定时任务调度。
    *   添加 API 接口供前端展示策略详情和收益曲线。
