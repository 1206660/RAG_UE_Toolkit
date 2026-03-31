"""将 data/raw 下的文档解析、分块并写入向量库（Chroma）。

支持增量入库（默认）和全量重建（--full）。
支持的文件格式：.md, .txt, .json, .ast
"""
from pathlib import Path
import sys
import json
import argparse
import hashlib

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from scripts.config import (
    DATA_RAW,
    INDEX_CHROMA,
    INDEX_META,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    COLLECTION_NAME,
    EMBEDDING_MODEL,
    CHROMA_ADD_BATCH_SIZE,
)

INGEST_STATE_FILE = INDEX_META / "ingest_state.json"


def split_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP):
    """按字符数分块，带重叠。"""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end].strip())
        start = end - overlap
    return [c for c in chunks if c]


def _load_state() -> dict:
    if not INGEST_STATE_FILE.exists():
        return {}
    try:
        return json.loads(INGEST_STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_state(state: dict) -> None:
    INDEX_META.mkdir(parents=True, exist_ok=True)
    INGEST_STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def _file_key(fp: Path) -> str:
    return str(fp.relative_to(DATA_RAW)).replace("\\", "/")


def _file_hash(fp: Path) -> str:
    """快速文件哈希，用于检测内容变化。"""
    h = hashlib.md5()
    with open(fp, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()[:12]


def main():
    import os

    parser = argparse.ArgumentParser(
        description="RAG UE Toolkit - 知识库入库（默认增量，仅处理新增/修改文件）"
    )
    parser.add_argument("--full", action="store_true", help="全量重建：忽略已入库状态，重新向量化并覆盖全部")
    parser.add_argument("--dry-run", action="store_true", help="仅扫描文件，不入库，显示待处理文件列表")
    args = parser.parse_args()
    full_rebuild = args.full
    dry_run = args.dry_run

    data_raw = DATA_RAW.resolve()
    index_chroma = INDEX_CHROMA.resolve()
    index_meta = INDEX_META.resolve()
    data_raw.mkdir(parents=True, exist_ok=True)
    if not dry_run:
        index_chroma.mkdir(parents=True, exist_ok=True)
        index_meta.mkdir(parents=True, exist_ok=True)

    # 扫描支持格式的文件
    exts = ("*.md", "*.txt", "*.json", "*.ast")
    all_files = []
    for ext in exts:
        all_files.extend(data_raw.glob(f"**/{ext}"))
    all_files = sorted(set(all_files))

    if not all_files:
        print(f"[提示] data/raw 下暂无 {', '.join(exts)} 文件。")
        print(f"       请将文档放入: {data_raw}")
        print(f"       支持：UE 蓝图 JSON 导出、ACF Wiki、UE 官方文档等")
        return

    print(f"[扫描] data/raw: {data_raw}")
    print(f"[扫描] 符合格式的文件: {len(all_files)} 个")

    # 按目录统计
    dir_counts = {}
    for fp in all_files:
        rel_dir = fp.relative_to(data_raw).parent.name if fp.relative_to(data_raw).parent != Path(".") else "(根目录)"
        dir_counts[rel_dir] = dir_counts.get(rel_dir, 0) + 1
    for d, c in sorted(dir_counts.items(), key=lambda x: -x[1]):
        print(f"       {d}: {c} 个文件")

    if dry_run:
        print(f"\n[预览] 以下文件将被处理（共 {len(all_files)} 个）：")
        for fp in all_files[:20]:
            print(f"       {fp.relative_to(data_raw)}")
        if len(all_files) > 20:
            print(f"       ... 还有 {len(all_files) - 20} 个文件")
        return

    # 计算待处理文件
    state = {} if full_rebuild else _load_state()
    to_process: list[Path] = []
    for fp in all_files:
        key = _file_key(fp)
        mtime = fp.stat().st_mtime
        fhash = _file_hash(fp)
        if full_rebuild or key not in state or state[key].get("hash") != fhash:
            to_process.append(fp)

    if not to_process:
        print("[完成] 无新增或修改文件，跳过向量化。")
        return

    # 初始化 Chroma
    client = chromadb.PersistentClient(
        path=str(index_chroma).replace("\\", "/"),
        settings=Settings(anonymized_telemetry=False),
    )
    if full_rebuild:
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass

    coll = client.get_or_create_collection(
        COLLECTION_NAME, metadata={"description": "RAG UE knowledge"}
    )
    if full_rebuild:
        print(f"[模式] 全量重建，共 {len(to_process)} 个文件待处理。")

    # 清理已删除文件的索引
    current_keys = {_file_key(fp) for fp in all_files}
    to_remove_keys = [k for k in state if k not in current_keys]
    if to_remove_keys and not full_rebuild:
        try:
            for key in to_remove_keys:
                res = coll.get(where={"source": key}, include=[])
                if res["ids"]:
                    coll.delete(ids=res["ids"])
                del state[key]
            if to_remove_keys:
                print(f"[清理] 从向量库移除已删除文件: {len(to_remove_keys)} 个。")
        except Exception:
            pass
        _save_state(state)

    print(f"[入库] 待处理: {len(to_process)} 个文件")

    # 文本分块
    def _doc_type(fp: Path) -> str:
        if fp.suffix.lower() == ".json":
            return "blueprint"
        if fp.suffix.lower() == ".ast":
            return "blueprint_ast"
        return "doc"

    all_chunks = []
    all_metas = []
    chunk_to_file_key = []
    for fp in to_process:
        text = fp.read_text(encoding="utf-8", errors="ignore")
        rel = fp.relative_to(data_raw)
        key = _file_key(fp)
        doc_type = _doc_type(fp)
        for i, chunk in enumerate(split_text(text)):
            all_chunks.append(chunk)
            all_metas.append({"source": key, "title": rel.stem, "type": doc_type})
            chunk_to_file_key.append(key)

    if not all_chunks:
        print("[提示] 待处理文件未得到任何文本块。")
        return

    # 删除本次要更新的文件在库中的旧块
    for key in {chunk_to_file_key[i] for i in range(len(chunk_to_file_key))}:
        res = coll.get(where={"source": key}, include=[])
        if res["ids"]:
            coll.delete(ids=res["ids"])

    print(f"[向量] 待向量化: {len(all_chunks)} 个文本块")
    print(f"[模型] {EMBEDDING_MODEL}")

    try:
        model = SentenceTransformer(EMBEDDING_MODEL, token=False)
    except Exception:
        print("\n[错误] 加载嵌入模型失败！")
        print("       首次运行需从 HuggingFace 下载模型 (~90MB)。")
        print("       如果网络受限，设置国内镜像：")
        print("         set HF_ENDPOINT=https://hf-mirror.com")
        print("       或:")
        print("         $env:HF_ENDPOINT='https://hf-mirror.com'")
        raise

    print("[进度] 正在向量化文本，请稍候...")
    embeddings = model.encode(all_chunks, show_progress_bar=True).tolist()

    # 分批写入 Chroma
    ids = [f"src:{chunk_to_file_key[i]}:{i}" for i in range(len(all_chunks))]
    n = len(all_chunks)
    for start in range(0, n, CHROMA_ADD_BATCH_SIZE):
        end = min(start + CHROMA_ADD_BATCH_SIZE, n)
        coll.add(
            ids=ids[start:end],
            embeddings=embeddings[start:end],
            documents=all_chunks[start:end],
            metadatas=all_metas[start:end],
        )
        if end < n:
            print(f"       已写入 {end}/{n} 条...")

    try:
        total = coll.count()
        print(f"\n[完成] 已入库 {len(all_chunks)} 个文本块，来源: {len(to_process)} 个文件")
        print(f"       向量库总条数: {total}")
    except Exception:
        print(f"\n[完成] 已入库 {len(all_chunks)} 个文本块，来源: {len(to_process)} 个文件")

    # 更新状态
    for fp in to_process:
        key = _file_key(fp)
        state[key] = {
            "mtime": fp.stat().st_mtime,
            "hash": _file_hash(fp),
            "chunk_count": sum(1 for k in chunk_to_file_key if k == key),
        }
    _save_state(state)


if __name__ == "__main__":
    main()
