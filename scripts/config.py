"""RAG UE Toolkit - 配置文件."""
from pathlib import Path

# 项目根目录
ROOT = Path(__file__).resolve().parent.parent

# 数据与索引路径
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
INDEX_CHROMA = ROOT / "index" / "chroma"
INDEX_META = ROOT / "index" / "meta"

# 分块参数
CHUNK_SIZE = 800          # 每块约 800 字符
CHUNK_OVERLAP = 150       # 块间重叠 150 字符

# 检索参数
TOP_K = 5                 # 检索返回条数
COLLECTION_NAME = "rag_ue"  # Chroma 集合名

# Chroma 单次 add 上限约 5461，入库时按批写入
CHROMA_ADD_BATCH_SIZE = 5000

# 嵌入模型（首次运行自动从 HuggingFace 下载，国内可设 HF_ENDPOINT 镜像）
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
