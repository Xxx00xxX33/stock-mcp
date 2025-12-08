# edgartools - SEC 财报 RAG/LLM 应用指南

## 1. 概述

**edgartools** 是一个专门为 LLM 和 RAG 应用设计的 Python 库，用于访问 SEC EDGAR 数据库中的美股公司财务报告。

### 核心特性
| 特性       | 说明                                                     |
| ---------- | -------------------------------------------------------- |
| 🏢 公司查询 | 通过股票代码（如 AAPL）自动查找公司信息                  |
| 📄 财报获取 | 支持 10-K、10-Q、8-K 等所有 SEC 表单类型                 |
| ✂️ 自动切分 | 内置 ChunkedDocument，自动将文档切分为 RAG 友好的 chunks |
| 📝 格式转换 | 支持 Markdown、纯文本、HTML 等多种输出格式               |
| 🎯 章节定位 | 可按 Item（章节）精准获取内容                            |

---

## 2. 安装与配置

```bash
# 安装
pip install edgartools

# SEC 要求设置身份标识
from edgar import set_identity
set_identity("Your Name your@email.com")
```

---

## 3. 基本用法

### 3.1 获取公司财报

```python
from edgar import Company, set_identity

set_identity("Your Name your@email.com")

# 初始化公司（自动查找 CIK）
company = Company("AAPL")

# 获取最新 10-K 年报
filing = company.get_filings(form="10-K").latest(1)

# 获取最新 10-Q 季报
quarterly = company.get_filings(form="10-Q").latest(1)

# 获取多份报告
last_5_10k = company.get_filings(form="10-K").latest(5)
```

### 3.2 转换为 Markdown

```python
# 直接转换（推荐用于 LLM）
markdown_content = filing.markdown()

# 保存文件
with open("AAPL_10K.md", "w", encoding="utf-8") as f:
    f.write(markdown_content)
```

### 3.3 其他格式

```python
# 纯文本
text_content = filing.text()

# 获取原始 HTML
html_content = filing.html()
```

---

## 4. RAG 核心功能：ChunkedDocument

这是 edgartools 最强大的功能，专为 RAG 应用设计。

### 4.1 获取 ChunkedDocument

```python
# Filing -> TenK 对象 -> ChunkedDocument
filing = Company("AAPL").get_filings(form="10-K").latest(1)
tenk = filing.obj()           # 转换为 TenK 对象
chunked_doc = tenk.doc        # 获取 ChunkedDocument
```

### 4.2 获取所有 Chunks

```python
# 获取所有 chunks（列表）
all_chunks = chunked_doc.chunks

print(f"总 chunks 数: {len(all_chunks)}")           # 约 299 个
print(f"平均大小: {chunked_doc.average_chunk_size()}")  # 约 888 字符
```

### 4.3 按章节获取 Chunks（精准检索）

```python
# 查看所有可用章节
print(chunked_doc.list_items())
# ['Item 1', 'Item 1A', 'Item 1B', 'Item 1C', 'Item 2', 'Item 3', 
#  'Item 4', 'Item 5', 'Item 6', 'Item 7', 'Item 7A', 'Item 8', 
#  'Item 9', 'Item 9A', 'Item 9B', 'Item 9C', 'Item 10', ...]

# 获取特定章节的 chunks
item1_chunks = list(chunked_doc.chunks_for_item('Item 1'))    # 业务描述
item1a_chunks = list(chunked_doc.chunks_for_item('Item 1A'))  # 风险因素
item7_chunks = list(chunked_doc.chunks_for_item('Item 7'))    # MD&A 管理层讨论
item8_chunks = list(chunked_doc.chunks_for_item('Item 8'))    # 财务报表
```

### 4.4 10-K 章节说明（重要）

| Item       | 名称                      | 内容说明             | RAG 推荐度 |
| ---------- | ------------------------- | -------------------- | ---------- |
| Item 1     | Business                  | 公司业务描述         | ⭐⭐⭐        |
| Item 1A    | Risk Factors              | 风险因素             | ⭐⭐⭐⭐⭐      |
| Item 1B    | Unresolved Staff Comments | 未解决的员工意见     | ⭐          |
| Item 1C    | Cybersecurity             | 网络安全             | ⭐⭐         |
| Item 2     | Properties                | 物业资产             | ⭐          |
| Item 3     | Legal Proceedings         | 法律诉讼             | ⭐⭐         |
| Item 5     | Market for Common Equity  | 股票市场信息         | ⭐⭐         |
| Item 6     | Selected Financial Data   | 精选财务数据         | ⭐⭐⭐        |
| **Item 7** | **MD&A**                  | **管理层讨论与分析** | ⭐⭐⭐⭐⭐      |
| Item 7A    | Quantitative Disclosures  | 市场风险量化披露     | ⭐⭐⭐        |
| **Item 8** | **Financial Statements**  | **财务报表**         | ⭐⭐⭐⭐⭐      |
| Item 9A    | Controls and Procedures   | 内部控制             | ⭐⭐         |

---

## 5. RAG 应用示例

### 5.1 存入向量数据库

```python
from edgar import Company, set_identity
# 假设使用 chromadb 或其他向量数据库

set_identity("Your Name your@email.com")

# 获取文档
filing = Company("AAPL").get_filings(form="10-K").latest(1)
chunked_doc = filing.obj().doc

# 只索引重要章节
important_items = ['Item 1', 'Item 1A', 'Item 7', 'Item 8']

documents = []
for item in important_items:
    for chunk in chunked_doc.chunks_for_item(item):
        documents.append({
            "text": chunk,
            "metadata": {
                "company": "AAPL",
                "form": "10-K",
                "item": item,
                "source": "SEC EDGAR"
            }
        })

print(f"准备索引 {len(documents)} 个文档块")

# 存入向量数据库
# vector_store.add_documents(documents)
```

### 5.2 精准问答

```python
def get_risk_factors(ticker: str) -> list:
    """获取公司风险因素用于 RAG"""
    filing = Company(ticker).get_filings(form="10-K").latest(1)
    chunked_doc = filing.obj().doc
    return list(chunked_doc.chunks_for_item('Item 1A'))

def get_management_discussion(ticker: str) -> list:
    """获取管理层讨论用于 RAG"""
    filing = Company(ticker).get_filings(form="10-K").latest(1)
    chunked_doc = filing.obj().doc
    return list(chunked_doc.chunks_for_item('Item 7'))
```

---

## 6. MCP 服务集成示例

```python
# filepath: edgar_mcp_tools.py
from edgar import Company, set_identity
from typing import List, Dict

set_identity("Your Name your@email.com")

def get_10k_chunks(ticker: str, items: List[str] = None) -> List[Dict]:
    """
    获取 10-K 报告的 chunks
    
    Args:
        ticker: 股票代码 (如 "AAPL")
        items: 要获取的章节列表，默认为全部
    
    Returns:
        包含 text 和 metadata 的 chunk 列表
    """
    filing = Company(ticker).get_filings(form="10-K").latest(1)
    tenk = filing.obj()
    chunked_doc = tenk.doc
    
    if items is None:
        # 返回所有 chunks
        return [{"text": chunk, "item": "all"} for chunk in chunked_doc.chunks]
    
    # 返回指定章节的 chunks
    result = []
    for item in items:
        for chunk in chunked_doc.chunks_for_item(item):
            result.append({
                "text": chunk,
                "item": item
            })
    return result

def get_10k_markdown(ticker: str) -> str:
    """获取 10-K 的完整 Markdown 内容"""
    filing = Company(ticker).get_filings(form="10-K").latest(1)
    return filing.markdown()

def list_available_items(ticker: str) -> List[str]:
    """列出 10-K 中所有可用章节"""
    filing = Company(ticker).get_filings(form="10-K").latest(1)
    chunked_doc = filing.obj().doc
    return chunked_doc.list_items()
```

---

## 7. 与 Java/Spring 集成

edgartools 是纯 Python 库，没有官方 Java 版本。推荐架构：

```
┌─────────────────────┐     REST/MCP      ┌──────────────────────┐
│   Spring AI         │ ◄───────────────► │  Python MCP Server   │
│   (Java)            │                   │  (edgartools)        │
└─────────────────────┘                   └──────────────────────┘
```

Python MCP 服务可以暴露以下端点供 Java 调用：
- `GET /edgar/{ticker}/10k/chunks` - 获取 chunks
- `GET /edgar/{ticker}/10k/markdown` - 获取 Markdown
- `GET /edgar/{ticker}/10k/items` - 列出可用章节

---

## 8. 性能与注意事项

### 8.1 SEC 速率限制
- SEC EDGAR 有速率限制，建议请求间隔 0.1 秒以上
- 必须设置有效的身份标识

### 8.2 缓存建议
```python
# 建议缓存已获取的文档
import functools

@functools.lru_cache(maxsize=100)
def get_cached_10k(ticker: str):
    return Company(ticker).get_filings(form="10-K").latest(1)
```

### 8.3 Chunk 大小
- 平均约 888 字符（约 200-300 tokens）
- 适合大多数 LLM 上下文窗口
- 如需更大/更小的 chunks，可能需要自行合并/拆分

---

## 9. 总结

| 功能            | 方法                                                                                                                     | 用途          |
| --------------- | ------------------------------------------------------------------------------------------------------------------------ | ------------- |
| 获取 Filing     | `Company(ticker).get_filings(form="10-K").latest(1)`                                                                     | 基础操作      |
| 转 Markdown     | `filing.markdown()`                                                                                                      | LLM 直接处理  |
| 获取所有 Chunks | `filing.obj().doc.chunks`                                                                                                | 全文 RAG 索引 |
| 按章节获取      | `chunked_doc.chunks_for_item('// filepath: /Users/huweihua/java/spring-ai-alibaba/stock-mcp/docs/edgartools-rag-guide.md |
# edgartools - SEC 财报 RAG/LLM 应用指南

## 1. 概述

**edgartools** 是一个专门为 LLM 和 RAG 应用设计的 Python 库，用于访问 SEC EDGAR 数据库中的美股公司财务报告。

### 核心特性
| 特性       | 说明                                                     |
| ---------- | -------------------------------------------------------- |
| 🏢 公司查询 | 通过股票代码（如 AAPL）自动查找公司信息                  |
| 📄 财报获取 | 支持 10-K、10-Q、8-K 等所有 SEC 表单类型                 |
| ✂️ 自动切分 | 内置 ChunkedDocument，自动将文档切分为 RAG 友好的 chunks |
| 📝 格式转换 | 支持 Markdown、纯文本、HTML 等多种输出格式               |
| 🎯 章节定位 | 可按 Item（章节）精准获取内容                            |

---

## 2. 安装与配置

```bash
# 安装
pip install edgartools

# SEC 要求设置身份标识
from edgar import set_identity
set_identity("Your Name your@email.com")
```

---

## 3. 基本用法

### 3.1 获取公司财报

```python
from edgar import Company, set_identity

set_identity("Your Name your@email.com")

# 初始化公司（自动查找 CIK）
company = Company("AAPL")

# 获取最新 10-K 年报
filing = company.get_filings(form="10-K").latest(1)

# 获取最新 10-Q 季报
quarterly = company.get_filings(form="10-Q").latest(1)

# 获取多份报告
last_5_10k = company.get_filings(form="10-K").latest(5)
```

### 3.2 转换为 Markdown

```python
# 直接转换（推荐用于 LLM）
markdown_content = filing.markdown()

# 保存文件
with open("AAPL_10K.md", "w", encoding="utf-8") as f:
    f.write(markdown_content)
```

### 3.3 其他格式

```python
# 纯文本
text_content = filing.text()

# 获取原始 HTML
html_content = filing.html()
```

---

## 4. RAG 核心功能：ChunkedDocument

这是 edgartools 最强大的功能，专为 RAG 应用设计。

### 4.1 获取 ChunkedDocument

```python
# Filing -> TenK 对象 -> ChunkedDocument
filing = Company("AAPL").get_filings(form="10-K").latest(1)
tenk = filing.obj()           # 转换为 TenK 对象
chunked_doc = tenk.doc        # 获取 ChunkedDocument
```

### 4.2 获取所有 Chunks

```python
# 获取所有 chunks（列表）
all_chunks = chunked_doc.chunks

print(f"总 chunks 数: {len(all_chunks)}")           # 约 299 个
print(f"平均大小: {chunked_doc.average_chunk_size()}")  # 约 888 字符
```

### 4.3 按章节获取 Chunks（精准检索）

```python
# 查看所有可用章节
print(chunked_doc.list_items())
# ['Item 1', 'Item 1A', 'Item 1B', 'Item 1C', 'Item 2', 'Item 3', 
#  'Item 4', 'Item 5', 'Item 6', 'Item 7', 'Item 7A', 'Item 8', 
#  'Item 9', 'Item 9A', 'Item 9B', 'Item 9C', 'Item 10', ...]

# 获取特定章节的 chunks
item1_chunks = list(chunked_doc.chunks_for_item('Item 1'))    # 业务描述
item1a_chunks = list(chunked_doc.chunks_for_item('Item 1A'))  # 风险因素
item7_chunks = list(chunked_doc.chunks_for_item('Item 7'))    # MD&A 管理层讨论
item8_chunks = list(chunked_doc.chunks_for_item('Item 8'))    # 财务报表
```

### 4.4 10-K 章节说明（重要）

| Item       | 名称                      | 内容说明             | RAG 推荐度 |
| ---------- | ------------------------- | -------------------- | ---------- |
| Item 1     | Business                  | 公司业务描述         | ⭐⭐⭐        |
| Item 1A    | Risk Factors              | 风险因素             | ⭐⭐⭐⭐⭐      |
| Item 1B    | Unresolved Staff Comments | 未解决的员工意见     | ⭐          |
| Item 1C    | Cybersecurity             | 网络安全             | ⭐⭐         |
| Item 2     | Properties                | 物业资产             | ⭐          |
| Item 3     | Legal Proceedings         | 法律诉讼             | ⭐⭐         |
| Item 5     | Market for Common Equity  | 股票市场信息         | ⭐⭐         |
| Item 6     | Selected Financial Data   | 精选财务数据         | ⭐⭐⭐        |
| **Item 7** | **MD&A**                  | **管理层讨论与分析** | ⭐⭐⭐⭐⭐      |
| Item 7A    | Quantitative Disclosures  | 市场风险量化披露     | ⭐⭐⭐        |
| **Item 8** | **Financial Statements**  | **财务报表**         | ⭐⭐⭐⭐⭐      |
| Item 9A    | Controls and Procedures   | 内部控制             | ⭐⭐         |

---

## 5. RAG 应用示例

### 5.1 存入向量数据库

```python
from edgar import Company, set_identity
# 假设使用 chromadb 或其他向量数据库

set_identity("Your Name your@email.com")

# 获取文档
filing = Company("AAPL").get_filings(form="10-K").latest(1)
chunked_doc = filing.obj().doc

# 只索引重要章节
important_items = ['Item 1', 'Item 1A', 'Item 7', 'Item 8']

documents = []
for item in important_items:
    for chunk in chunked_doc.chunks_for_item(item):
        documents.append({
            "text": chunk,
            "metadata": {
                "company": "AAPL",
                "form": "10-K",
                "item": item,
                "source": "SEC EDGAR"
            }
        })

print(f"准备索引 {len(documents)} 个文档块")

# 存入向量数据库
# vector_store.add_documents(documents)
```

### 5.2 精准问答

```python
def get_risk_factors(ticker: str) -> list:
    """获取公司风险因素用于 RAG"""
    filing = Company(ticker).get_filings(form="10-K").latest(1)
    chunked_doc = filing.obj().doc
    return list(chunked_doc.chunks_for_item('Item 1A'))

def get_management_discussion(ticker: str) -> list:
    """获取管理层讨论用于 RAG"""
    filing = Company(ticker).get_filings(form="10-K").latest(1)
    chunked_doc = filing.obj().doc
    return list(chunked_doc.chunks_for_item('Item 7'))
```

---

## 6. MCP 服务集成示例

```python
# filepath: edgar_mcp_tools.py
from edgar import Company, set_identity
from typing import List, Dict

set_identity("Your Name your@email.com")

def get_10k_chunks(ticker: str, items: List[str] = None) -> List[Dict]:
    """
    获取 10-K 报告的 chunks
    
    Args:
        ticker: 股票代码 (如 "AAPL")
        items: 要获取的章节列表，默认为全部
    
    Returns:
        包含 text 和 metadata 的 chunk 列表
    """
    filing = Company(ticker).get_filings(form="10-K").latest(1)
    tenk = filing.obj()
    chunked_doc = tenk.doc
    
    if items is None:
        # 返回所有 chunks
        return [{"text": chunk, "item": "all"} for chunk in chunked_doc.chunks]
    
    # 返回指定章节的 chunks
    result = []
    for item in items:
        for chunk in chunked_doc.chunks_for_item(item):
            result.append({
                "text": chunk,
                "item": item
            })
    return result

def get_10k_markdown(ticker: str) -> str:
    """获取 10-K 的完整 Markdown 内容"""
    filing = Company(ticker).get_filings(form="10-K").latest(1)
    return filing.markdown()

def list_available_items(ticker: str) -> List[str]:
    """列出 10-K 中所有可用章节"""
    filing = Company(ticker).get_filings(form="10-K").latest(1)
    chunked_doc = filing.obj().doc
    return chunked_doc.list_items()
```

---

## 7. 与 Java/Spring 集成

edgartools 是纯 Python 库，没有官方 Java 版本。推荐架构：

```
┌─────────────────────┐     REST/MCP      ┌──────────────────────┐
│   Spring AI         │ ◄───────────────► │  Python MCP Server   │
│   (Java)            │                   │  (edgartools)        │
└─────────────────────┘                   └──────────────────────┘
```

Python MCP 服务可以暴露以下端点供 Java 调用：
- `GET /edgar/{ticker}/10k/chunks` - 获取 chunks
- `GET /edgar/{ticker}/10k/markdown` - 获取 Markdown
- `GET /edgar/{ticker}/10k/items` - 列出可用章节

---

## 8. 性能与注意事项

### 8.1 SEC 速率限制
- SEC EDGAR 有速率限制，建议请求间隔 0.1 秒以上
- 必须设置有效的身份标识

### 8.2 缓存建议
```python
# 建议缓存已获取的文档
import functools

@functools.lru_cache(maxsize=100)
def get_cached_10k(ticker: str):
    return Company(ticker).get_filings(form="10-K").latest(1)
```

### 8.3 Chunk 大小
- 平均约 888 字符（约 200-300 tokens）
- 适合大多数 LLM 上下文窗口
- 如需更大/更小的 chunks，可能需要自行合并/拆分

---

## 9. 总结

| 功能            | 方法                                                 | 用途          |
| --------------- | ---------------------------------------------------- | ------------- |
| 获取 Filing     | `Company(ticker).get_filings(form="10-K").latest(1)` | 基础操作      |
| 转 Markdown     | `filing.markdown()`                                  | LLM 直接处理  |
| 获取所有 Chunks | `filing.obj().doc.chunks`                            | 全文 RAG 索引 |
| 按章节获取      | `chunked_doc.chunks_for_item('                       |