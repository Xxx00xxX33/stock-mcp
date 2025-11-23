"""
使用阿里百炼（DashScope）测试 MCP Streamable HTTP 服务器
"""
import asyncio
import os
import json
from typing import Any

# 设置 API Key
os.environ["DASHSCOPE_API_KEY"] = "your-token"

# 清除代理设置
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)
os.environ.pop("all_proxy", None)
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("ALL_PROXY", None)

import httpx
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

# MCP 服务器配置
MCP_SERVER_URL = "http://localhost:9898"


async def call_mcp_tool(tool_name: str, arguments: dict) -> dict:
    """调用 MCP 工具（Streamable HTTP 协议）"""
    async with httpx.AsyncClient(trust_env=False, timeout=60.0) as client:
        response = await client.post(
            f"{MCP_SERVER_URL}/?_tool={tool_name}",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream"
            },
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                },
                "id": "test-1"
            }
        )
        response.raise_for_status()
        return parse_sse_response(response.text)


def parse_sse_response(text: str) -> dict:
    """解析 SSE 格式的响应"""
    lines = text.strip().split('\n')
    for line in lines:
        if line.startswith('data: '):
            data_str = line[6:]  # 移除 'data: ' 前缀
            return json.loads(data_str)
    raise ValueError("No data found in SSE response")


async def list_mcp_tools() -> list[dict]:
    """列出所有可用的 MCP 工具"""
    async with httpx.AsyncClient(trust_env=False, timeout=60.0) as client:
        response = await client.post(
            MCP_SERVER_URL,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream"
            },
            json={
                "jsonrpc": "2.0",
                "method": "tools/list",
                "params": {},
                "id": "list-tools"
            }
        )
        response.raise_for_status()
        
        # 解析 SSE 响应
        result = parse_sse_response(response.text)
        return result.get("result", {}).get("tools", [])


async def main():
    print("🚀 开始测试 MCP + 阿里百炼集成...")
    
    # 1. 列出可用工具
    print(f"\n🔌 连接到 MCP 服务器: {MCP_SERVER_URL}")
    tools = await list_mcp_tools()
    print(f"✅ 发现 {len(tools)} 个工具")
    
    # 转换为 LangChain 工具格式
    lc_tools = []
    for tool in tools:
        lc_tool = {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool.get("description", ""),
                "parameters": tool.get("inputSchema", {})
            }
        }
        lc_tools.append(lc_tool)
        print(f"  - {tool['name']}")
    
    # 2. 初始化阿里百炼模型
    print("\n🤖 初始化阿里百炼 (Qwen)...")
    llm = ChatTongyi(model="qwen-turbo")
    llm_with_tools = llm.bind_tools(lc_tools)
    
    # 3. 执行测试查询
    # 明确告诉 LLM 使用 EXCHANGE:SYMBOL 格式
    query = """帮我查一下贵州茅台现在的价格，并分析一下它的基本面情况。

重要提示：
- 查询股票时，ticker 参数必须使用 "交易所:股票代码" 格式
- 贵州茅台的正确格式是：SSE:600519
- 其他示例：NASDAQ:BABA (阿里巴巴), NYSE:TSLA (特斯拉), SZSE:000001 (平安银行)
"""
    print(f"\n❓ 用户查询: {query}")
    
    messages = [HumanMessage(content=query)]
    
    # 第一次 LLM 调用 - 决定调用哪些工具
    print("⏳ LLM 正在思考...")
    response = llm_with_tools.invoke(messages)
    messages.append(response)
    
    # 检查是否调用了工具
    if response.tool_calls:
        print(f"\n🛠️  LLM 决定调用 {len(response.tool_calls)} 个工具:")
        
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_call_id = tool_call["id"]
            
            print(f"\n  > 调用工具: {tool_name}")
            print(f"    参数: {json.dumps(tool_args, ensure_ascii=False)}")
            
            # 通过 MCP 执行工具
            try:
                result = await call_mcp_tool(tool_name, tool_args)
                
                # 提取工具结果 - MCP 返回格式: result.content[0].text
                if "result" in result and "content" in result["result"]:
                    content_items = result["result"]["content"]
                    if content_items and len(content_items) > 0:
                        # 获取第一个 content 项的 text
                        tool_output = content_items[0].get("text", "")
                        print(f"    ✅ 结果: {tool_output[:200]}...")
                    else:
                        tool_output = json.dumps(result, ensure_ascii=False)
                        print(f"    ⚠️  空内容")
                else:
                    tool_output = json.dumps(result, ensure_ascii=False)
                    print(f"    ⚠️  意外格式: {tool_output[:200]}...")
                
                # 添加工具结果到消息历史
                messages.append(ToolMessage(
                    content=tool_output,
                    tool_call_id=tool_call_id
                ))
            except Exception as e:
                print(f"    ❌ 工具调用失败: {e}")
                import traceback
                traceback.print_exc()
                messages.append(ToolMessage(
                    content=f"工具调用失败: {str(e)}",
                    tool_call_id=tool_call_id
                ))
        
        # 第二次 LLM 调用 - 生成最终答案
        print("\n⏳ LLM 正在生成最终答案...")
        final_response = llm_with_tools.invoke(messages)
        
        print("\n" + "="*60)
        print("💡 最终答案:")
        print("="*60)
        print(final_response.content)
        print("="*60)
    else:
        print("\n⚠️  LLM 没有调用任何工具")
        print(response.content)


if __name__ == "__main__":
    asyncio.run(main())
