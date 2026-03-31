# 🎮 RAG UE Toolkit

**Unreal Engine 知识库检索工具** - 基于 RAG（检索增强生成）的 UE 开发文档向量检索系统

支持蓝图 JSON/AST、ACF 插件文档、UE 官方文档等多种数据源，为 AI 编程助手（Cursor、WorkBuddy）提供上下文检索能力。

---

## ✨ 特性

- 🔍 **语义检索**: 基于 sentence-transformers 的向量相似度搜索
- 📦 **增量入库**: 自动检测文件变化，只处理新增/修改文件
- 🌐 **Web 界面**: Streamlit 可视化查询与数据管理
- 🤖 **MCP 集成**: 支持 Cursor/WorkBuddy 等 AI 工具通过 MCP 协议调用
- 📊 **多格式支持**: `.md`, `.txt`, `.json`, `.ast`（蓝图导出）
- 🚀 **一键安装**: 自动配置 Python 环境和依赖

---

## 🚀 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/1206660/RAG_UE_Toolkit.git
cd RAG_UE_Toolkit
```

### 2. 一键安装

**Windows**:
```cmd
install.bat
```

**Linux/macOS**:
```bash
chmod +x install.sh
./install.sh
```

安装脚本会自动：
- 创建 Python 虚拟环境（`.venv/`）
- 安装依赖包（~1.3GB，包含 PyTorch）
- 初始化项目目录结构

> 💡 **国内网络加速**:
> ```bash
> # Pip 镜像
> set PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/
> 
> # HuggingFace 镜像（首次下载模型时）
> set HF_ENDPOINT=https://hf-mirror.com
> ```

### 3. 准备数据源

将文档放入 `data/raw/` 目录：

```
data/raw/
├── ACF-SlimWiki/          # ACF 插件 Wiki（Markdown）
├── BlueprintNodes/        # UE 蓝图节点文档
└── Blueprint/             # 你的项目蓝图 JSON/AST 导出
```

支持格式：
- **Markdown (`.md`)**: 文档、Wiki、笔记
- **Text (`.txt`)**: 纯文本文档
- **JSON (`.json`)**: UE 蓝图导出（结构化）
- **AST (`.ast`)**: UE 蓝图 AST 树

### 4. 入库数据

**首次入库（全量）**:
```bash
.venv\Scripts\python scripts\ingest.py --full
```

**增量更新**（仅处理新增/修改文件）:
```bash
.venv\Scripts\python scripts\ingest.py
```

首次运行会自动下载嵌入模型 `sentence-transformers/all-MiniLM-L6-v2` (~90MB)，缓存后不再重复下载。

### 5. 使用

#### 方式 A: Web 界面（推荐）

```bash
.venv\Scripts\streamlit run scripts\app.py
```

浏览器自动打开 `http://localhost:8501`，提供：
- 📊 知识库状态监控
- 🔍 可视化查询与结果展示
- 📦 数据源管理
- 🚀 一键入库操作

#### 方式 B: 命令行查询

```bash
.venv\Scripts\python scripts\query.py "蓝图 Tick 性能优化"
```

#### 方式 C: MCP 集成（供 AI 工具使用）

在 Cursor 项目根目录创建 `.cursor/mcp.json`：

```json
{
  "mcpServers": {
    "rag-ue": {
      "command": "python",
      "args": ["scripts/mcp_server.py"],
      "cwd": "D:\\Code\\RAG_UE_Toolkit"
    }
  }
}
```

WorkBuddy 配置类似（在设置中添加 MCP Server）。

配置后，AI 助手可通过 `rag_query` 工具检索知识库。

---

## 📦 项目结构

```
RAG_UE_Toolkit/
├── scripts/
│   ├── config.py         # 配置（路径、分块、模型）
│   ├── ingest.py         # 入库脚本（支持增量/全量）
│   ├── query.py          # 查询脚本（CLI）
│   ├── mcp_server.py     # MCP 服务（供 AI 工具调用）
│   └── app.py            # Streamlit Web 界面
├── data/
│   └── raw/              # 原始文档（用户自行准备）
│       ├── ACF-SlimWiki/
│       ├── BlueprintNodes/
│       └── Blueprint/
├── index/
│   ├── chroma/           # ChromaDB 向量索引（自动生成）
│   └── meta/             # 入库状态记录（自动生成）
├── requirements.txt      # Python 依赖
├── install.bat           # Windows 一键安装
├── install.sh            # Linux/macOS 一键安装
├── .gitignore
├── LICENSE
└── README.md
```

---

## 🔧 技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| **向量数据库** | [ChromaDB](https://www.trychroma.com/) | 持久化向量存储 |
| **嵌入模型** | [sentence-transformers/all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) | 轻量级语义向量模型 |
| **Web 界面** | [Streamlit](https://streamlit.io/) | 快速构建交互式界面 |
| **MCP 协议** | [mcp](https://github.com/modelcontextprotocol/python-sdk) | Model Context Protocol |
| **Python** | 3.8+ | 运行环境 |

---

## 📖 使用说明

### 命令行工具

#### 入库脚本 (`ingest.py`)

```bash
# 增量入库（默认）
python scripts/ingest.py

# 全量重建（清空向量库重新入库）
python scripts/ingest.py --full

# 预览待处理文件（不实际入库）
python scripts/ingest.py --dry-run
```

#### 查询脚本 (`query.py`)

```bash
# 查询问题
python scripts/query.py "ACF 战斗系统架构"

# 返回更多结果（默认 5 条）
python scripts/query.py "蓝图性能优化" --top-k 10
```

#### MCP 服务 (`mcp_server.py`)

```bash
# 直接运行（stdio 模式）
python scripts/mcp_server.py
```

供 Cursor/WorkBuddy 等工具通过 MCP 协议调用，不需要手动运行。

---

## ⚙️ 配置说明

编辑 `scripts/config.py` 自定义参数：

```python
# 分块参数
CHUNK_SIZE = 800          # 每块字符数
CHUNK_OVERLAP = 150       # 块间重叠字符数

# 检索参数
TOP_K = 5                 # 默认返回条数
COLLECTION_NAME = "rag_ue"  # ChromaDB 集合名

# 嵌入模型（可改为其他 sentence-transformers 模型）
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
```

---

## 🐛 常见问题

### 1. 首次运行报错 "加载嵌入模型失败"

**原因**: 需从 HuggingFace 下载模型 (~90MB)

**解决**: 设置国内镜像后重试
```bash
set HF_ENDPOINT=https://hf-mirror.com
python scripts/ingest.py --full
```

### 2. 向量库为空 / 检索无结果

**原因**: 未入库数据或 `data/raw/` 为空

**解决**:
1. 确认 `data/raw/` 下有文档文件
2. 运行 `python scripts/ingest.py --full`

### 3. MCP 连接失败

**检查清单**:
- ✅ Python 虚拟环境已激活（`.venv/Scripts/python.exe`）
- ✅ `cwd` 路径正确（指向 RAG_UE_Toolkit 根目录）
- ✅ 向量库已初始化（运行过 `ingest.py --full`）
- ✅ Cursor/WorkBuddy 已重启（配置修改后需重启）

### 4. Streamlit 界面无法启动

**解决**:
```bash
# 确认 streamlit 已安装
.venv\Scripts\pip install streamlit

# 指定端口启动
.venv\Scripts\streamlit run scripts\app.py --server.port 8502
```

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

建议贡献方向：
- 🌐 支持更多文档格式（PDF、HTML、Docx）
- 🔍 增强查询能力（过滤、排序、高亮）
- 🎨 改进 Web 界面 UI/UX
- 📊 添加数据统计与可视化
- 🌍 多语言支持

---

## 📄 开源协议

[MIT License](LICENSE)

---

## 🙏 致谢

- [ChromaDB](https://www.trychroma.com/) - 高效向量数据库
- [Sentence Transformers](https://www.sbert.net/) - 开源嵌入模型
- [Streamlit](https://streamlit.io/) - 快速构建数据应用
- [MCP Protocol](https://github.com/modelcontextprotocol) - AI 工具协议标准

---

## 📮 联系方式

- GitHub: [@1206660](https://github.com/1206660)
- Issues: [提交问题](https://github.com/1206660/RAG_UE_Toolkit/issues)

---

**⭐ 如果这个工具对你有帮助，请给个 Star！**
