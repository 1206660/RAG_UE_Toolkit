"""
RAG UE Toolkit - MCP 查询服务。

供 AI 编程助手（Cursor、WorkBuddy 等）通过 MCP 协议调用知识库检索。

运行方式：
  .venv\\Scripts\\python scripts\\mcp_server.py

Cursor 配置（.cursor/mcp.json）：
  {
    "mcpServers": {
      "rag-ue": {
        "command": "python",
        "args": ["scripts/mcp_server.py"],
        "cwd": "D:\\Code\\RAG_UE_Toolkit"
      }
    }
  }

WorkBuddy / Claude Desktop 配置类似，使用 stdio transport。
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# MCP 服务不要往 stdout 打日志，会破坏 JSON-RPC
import logging
logging.basicConfig(level=logging.WARNING, stream=sys.stderr)

from mcp.server.fastmcp import FastMCP
from scripts.query import query_rag

mcp = FastMCP("RAG UE Toolkit")


@mcp.tool()
def rag_query(query: str, top_k: int = 5, max_chunk_chars: int = 2000) -> str:
    """
    在 RAG UE 知识库中检索与问题最相关的文档片段。
    知识库包含：UE 蓝图信息（JSON/AST）、ACF 插件文档、UE 官方节点文档等。

    :param query: 要检索的问题或关键词（例如：「蓝图 Tick 性能优化」「ACF 战斗系统」「GAS 属性复制」）
    :param top_k: 返回的最相关条数，默认 5
    :param max_chunk_chars: 每条片段最大字符数，超出会截断，默认 2000
    :return: Markdown 格式的检索结果
    """
    results = query_rag(query, top_k=top_k, max_chunk_chars=max_chunk_chars)
    if not results:
        return "未检索到相关片段，请换关键词或先执行: python scripts/ingest.py --full"
    lines = [f"## 检索到 {len(results)} 条相关片段\n"]
    for i, item in enumerate(results, 1):
        lines.append(f"### [{i}] {item['source']} (type: {item['type']})")
        lines.append("")
        lines.append(item["content"])
        lines.append("")
    return "\n".join(lines).strip()


if __name__ == "__main__":
    mcp.run(transport="stdio")
