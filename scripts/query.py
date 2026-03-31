"""从向量库检索与 query 最相关的片段（Top-K）。

可被 CLI、MCP Server 或其他 Python 脚本调用。
"""
from pathlib import Path
import sys
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from scripts.config import INDEX_CHROMA, TOP_K, COLLECTION_NAME, EMBEDDING_MODEL

# 懒加载，供 MCP 与多次调用复用
_model = None
_client = None


def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL, token=False)
    return _model


def _get_client():
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(
            path=str(INDEX_CHROMA), settings=Settings(anonymized_telemetry=False)
        )
    return _client


def query_rag(
    query: str,
    top_k: Optional[int] = None,
    max_chunk_chars: Optional[int] = None,
) -> list[dict]:
    """
    在 RAG 知识库中检索与 query 最相关的片段。
    :param query: 查询字符串
    :param top_k: 返回条数，默认使用 config 中的 TOP_K
    :param max_chunk_chars: 每条内容最大字符数，None 表示不截断
    :return: [{"content": str, "source": str, "title": str, "type": str}, ...]
    """
    k = top_k if top_k is not None else TOP_K
    model = _get_model()
    client = _get_client()
    coll = client.get_collection(COLLECTION_NAME)
    q_emb = model.encode([query]).tolist()
    res = coll.query(
        query_embeddings=q_emb, n_results=k, include=["documents", "metadatas"]
    )
    out = []
    for doc, meta in zip(res["documents"][0], res["metadatas"][0]):
        content = doc
        if max_chunk_chars is not None and len(content) > max_chunk_chars:
            content = content[:max_chunk_chars] + "..."
        out.append({
            "content": content,
            "source": meta.get("source", ""),
            "title": meta.get("title", ""),
            "type": meta.get("type", "doc"),
        })
    return out


def main():
    if len(sys.argv) < 2:
        print("用法: python scripts/query.py \"你的问题\"")
        print("示例: python scripts/query.py \"蓝图 Tick 性能优化\"")
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    print(f"Query: {query}\n")

    results = query_rag(query, max_chunk_chars=500)
    if not results:
        print("未检索到相关片段。请先运行: python scripts/ingest.py --full")
        return

    for i, item in enumerate(results, 1):
        print(f"--- [{i}] source: {item['source']} (type: {item['type']}) ---")
        print(item["content"])
        print()


if __name__ == "__main__":
    main()
