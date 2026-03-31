"""
RAG UE Toolkit - Web 界面

运行方式：
  streamlit run scripts/app.py

功能：
- 📊 知识库状态监控
- 🔍 可视化查询与结果展示
- 📦 数据源管理
- 🚀 一键入库操作
"""
import streamlit as st
from pathlib import Path
import sys
import json
from datetime import datetime
import subprocess

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.config import DATA_RAW, INDEX_CHROMA, INDEX_META, COLLECTION_NAME
from scripts.query import query_rag

st.set_page_config(
    page_title="RAG UE Toolkit",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==================== 侧边栏：系统状态 ====================
with st.sidebar:
    st.title("🎮 RAG UE Toolkit")
    st.caption("Unreal Engine 知识库检索工具")
    
    st.divider()
    st.subheader("📊 系统状态")
    
    # 检查数据源
    data_raw_path = DATA_RAW.resolve()
    if data_raw_path.exists():
        exts = ("*.md", "*.txt", "*.json", "*.ast")
        all_files = []
        for ext in exts:
            all_files.extend(data_raw_path.glob(f"**/{ext}"))
        file_count = len(set(all_files))
        st.success(f"✅ 数据源: {file_count} 个文件")
        
        # 按子目录统计
        dir_counts = {}
        for fp in all_files:
            rel = fp.relative_to(data_raw_path)
            top_dir = rel.parts[0] if len(rel.parts) > 1 else "(根目录)"
            dir_counts[top_dir] = dir_counts.get(top_dir, 0) + 1
        
        with st.expander("📁 数据源分布", expanded=False):
            for d, c in sorted(dir_counts.items(), key=lambda x: -x[1]):
                st.text(f"{d}: {c} 个")
    else:
        st.warning("⚠️ 数据源目录不存在")
        st.caption(f"路径: {data_raw_path}")
    
    # 检查向量库
    index_path = INDEX_CHROMA.resolve()
    if index_path.exists():
        try:
            import chromadb
            from chromadb.config import Settings
            client = chromadb.PersistentClient(
                path=str(index_path),
                settings=Settings(anonymized_telemetry=False)
            )
            coll = client.get_collection(COLLECTION_NAME)
            count = coll.count()
            st.success(f"✅ 向量库: {count:,} 条")
            
            # 索引大小
            try:
                size = sum(f.stat().st_size for f in index_path.rglob("*") if f.is_file())
                size_mb = size / (1024 * 1024)
                st.caption(f"大小: {size_mb:.1f} MB")
            except:
                pass
        except Exception as e:
            st.error("❌ 向量库未初始化")
            st.caption(str(e)[:50])
    else:
        st.warning("⚠️ 向量库未创建")
    
    # 入库状态
    state_file = INDEX_META / "ingest_state.json"
    if state_file.exists():
        try:
            state = json.loads(state_file.read_text(encoding="utf-8"))
            st.info(f"📝 已入库: {len(state)} 个文件")
        except:
            pass
    
    st.divider()
    st.subheader("⚙️ 操作")
    
    if st.button("🚀 增量入库", use_container_width=True):
        with st.spinner("正在入库..."):
            try:
                result = subprocess.run(
                    [sys.executable, "scripts/ingest.py"],
                    cwd=str(ROOT),
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                if result.returncode == 0:
                    st.success("✅ 入库完成")
                    st.code(result.stdout, language="text")
                    st.rerun()
                else:
                    st.error("❌ 入库失败")
                    st.code(result.stderr, language="text")
            except Exception as e:
                st.error(f"错误: {str(e)}")
    
    if st.button("🔄 全量重建", use_container_width=True):
        with st.spinner("正在全量重建..."):
            try:
                result = subprocess.run(
                    [sys.executable, "scripts/ingest.py", "--full"],
                    cwd=str(ROOT),
                    capture_output=True,
                    text=True,
                    timeout=600
                )
                if result.returncode == 0:
                    st.success("✅ 重建完成")
                    st.code(result.stdout, language="text")
                    st.rerun()
                else:
                    st.error("❌ 重建失败")
                    st.code(result.stderr, language="text")
            except Exception as e:
                st.error(f"错误: {str(e)}")
    
    st.divider()
    st.caption("v1.0.0 | MIT License")

# ==================== 主界面：查询与结果 ====================
tab1, tab2, tab3 = st.tabs(["🔍 知识检索", "📦 数据管理", "📖 使用说明"])

with tab1:
    st.header("🔍 知识检索")
    
    # 查询输入
    col1, col2 = st.columns([4, 1])
    with col1:
        query_text = st.text_input(
            "输入问题或关键词",
            placeholder="例如：蓝图 Tick 性能优化、ACF 战斗系统、GAS 属性复制",
            label_visibility="collapsed"
        )
    with col2:
        top_k = st.number_input("返回条数", min_value=1, max_value=20, value=5, label_visibility="collapsed")
    
    # 预设问题
    st.caption("💡 快速问题:")
    preset_cols = st.columns(4)
    preset_questions = [
        "蓝图 Tick 性能问题",
        "ACF 战斗系统架构",
        "GAS Gameplay Ability",
        "Nanite 使用限制"
    ]
    for idx, q in enumerate(preset_questions):
        if preset_cols[idx].button(q, key=f"preset_{idx}"):
            query_text = q
    
    # 执行查询
    if query_text:
        with st.spinner("🔍 检索中..."):
            try:
                results = query_rag(query_text, top_k=top_k, max_chunk_chars=None)
                
                if results:
                    st.success(f"✅ 检索到 {len(results)} 条相关片段")
                    
                    for i, item in enumerate(results, 1):
                        with st.expander(f"**[{i}]** {item['title']} ({item['type']})", expanded=(i==1)):
                            st.caption(f"📄 来源: `{item['source']}`")
                            st.markdown("---")
                            st.markdown(item['content'])
                            
                            # 复制按钮
                            st.code(item['content'], language="text")
                else:
                    st.warning("未检索到相关片段，请先入库数据或更换关键词")
            except Exception as e:
                st.error(f"❌ 检索失败: {str(e)}")
                st.caption("请确认向量库已初始化，运行: `python scripts/ingest.py --full`")

with tab2:
    st.header("📦 数据源管理")
    
    st.subheader("📁 data/raw 目录结构")
    st.caption(f"路径: {DATA_RAW.resolve()}")
    
    if DATA_RAW.exists():
        # 递归显示目录树
        def show_tree(path: Path, prefix="", max_depth=3, current_depth=0):
            if current_depth >= max_depth:
                return
            
            try:
                items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
                for idx, item in enumerate(items[:50]):  # 限制显示数量
                    is_last = idx == len(items) - 1
                    connector = "└── " if is_last else "├── "
                    
                    if item.is_dir():
                        file_count = len(list(item.rglob("*")))
                        st.text(f"{prefix}{connector}📁 {item.name}/ ({file_count} 项)")
                        new_prefix = prefix + ("    " if is_last else "│   ")
                        show_tree(item, new_prefix, max_depth, current_depth + 1)
                    else:
                        size_kb = item.stat().st_size / 1024
                        st.text(f"{prefix}{connector}📄 {item.name} ({size_kb:.1f} KB)")
            except PermissionError:
                st.text(f"{prefix}[权限不足]")
        
        show_tree(DATA_RAW, max_depth=2)
    else:
        st.warning("⚠️ data/raw 目录不存在")
        if st.button("📁 创建 data/raw 目录"):
            DATA_RAW.mkdir(parents=True, exist_ok=True)
            st.success("✅ 目录已创建")
            st.rerun()
    
    st.divider()
    st.subheader("📊 入库历史")
    
    state_file = INDEX_META / "ingest_state.json"
    if state_file.exists():
        state = json.loads(state_file.read_text(encoding="utf-8"))
        st.json(state, expanded=False)
    else:
        st.info("尚无入库记录")

with tab3:
    st.header("📖 使用说明")
    
    st.markdown("""
## 🚀 快速开始

### 1. 准备数据源
将文档放入 `data/raw/` 目录：
- **UE 蓝图 JSON/AST**: 导出的蓝图结构文件
- **ACF Wiki**: ACF 插件文档（Markdown）
- **UE 官方文档**: 蓝图节点、API 文档

支持格式：`.md`, `.txt`, `.json`, `.ast`

### 2. 入库数据
点击侧边栏 **🚀 增量入库** 或运行命令：
```bash
python scripts/ingest.py
```

首次入库或数据大改时，使用 **🔄 全量重建**：
```bash
python scripts/ingest.py --full
```

### 3. 检索知识
在 **🔍 知识检索** 标签页输入问题，即可获得相关文档片段。

---

## 🔧 MCP 集成（供 AI 编程助手使用）

### Cursor 配置
在项目根目录创建 `.cursor/mcp.json`：
```json
{
  "mcpServers": {
    "rag-ue": {
      "command": "python",
      "args": ["scripts/mcp_server.py"],
      "cwd": "D:\\\\Code\\\\RAG_UE_Toolkit"
    }
  }
}
```

### WorkBuddy 配置
在 WorkBuddy 设置中添加 MCP Server：
```json
{
  "command": "python",
  "args": ["scripts/mcp_server.py"],
  "cwd": "D:/Code/RAG_UE_Toolkit",
  "transport": "stdio"
}
```

---

## 📦 数据结构

```
RAG_UE_Toolkit/
├── data/
│   └── raw/              # 原始文档（自行准备）
│       ├── ACF-SlimWiki/
│       ├── BlueprintNodes/
│       └── Blueprint/
├── index/
│   ├── chroma/           # 向量索引（自动生成）
│   └── meta/             # 入库状态（自动生成）
└── scripts/
    ├── config.py
    ├── ingest.py
    ├── query.py
    ├── mcp_server.py
    └── app.py            # 本界面
```

---

## ⚠️ 常见问题

### 1. 首次运行报错 "加载嵌入模型失败"
**原因**: 需从 HuggingFace 下载模型 (~90MB)

**解决**: 国内网络设置镜像：
```bash
set HF_ENDPOINT=https://hf-mirror.com
```
或 PowerShell：
```powershell
$env:HF_ENDPOINT='https://hf-mirror.com'
```

### 2. 向量库为空
运行 **🔄 全量重建** 或命令：
```bash
python scripts/ingest.py --full
```

### 3. MCP 连接失败
检查：
- Python 环境已激活（`.venv/Scripts/python.exe`）
- `cwd` 路径正确
- 向量库已初始化

---

## 📝 技术栈
- **向量库**: ChromaDB
- **嵌入模型**: sentence-transformers/all-MiniLM-L6-v2
- **Web 界面**: Streamlit
- **MCP 协议**: mcp (Model Context Protocol)
    """)
    
    st.divider()
    st.info("💡 提示：首次运行需要下载约 90MB 的嵌入模型（自动缓存）")

# ==================== 页脚 ====================
st.divider()
st.caption("RAG UE Toolkit | 基于 ChromaDB + Sentence Transformers | [GitHub](https://github.com/1206660/RAG_UE_Toolkit)")
