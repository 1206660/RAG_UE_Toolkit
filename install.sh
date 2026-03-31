#!/bin/bash

echo "========================================"
echo "  RAG UE Toolkit - 一键安装"
echo "========================================"
echo

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未找到 Python3，请先安装 Python 3.8+"
    exit 1
fi

echo "[1/4] 检测到 Python:"
python3 --version
echo

# 创建虚拟环境
if [ ! -d ".venv" ]; then
    echo "[2/4] 创建虚拟环境..."
    python3 -m venv .venv
    if [ $? -ne 0 ]; then
        echo "[错误] 创建虚拟环境失败"
        exit 1
    fi
    echo "✅ 虚拟环境已创建"
else
    echo "[2/4] 虚拟环境已存在，跳过创建"
fi
echo

# 激活虚拟环境并安装依赖
echo "[3/4] 安装 Python 依赖包..."
echo "提示：首次安装需下载 ~1.3GB（包含 PyTorch）"
echo

source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo
    echo "[错误] 依赖安装失败！"
    echo "常见原因："
    echo "  1. 网络问题 - 尝试设置 pip 镜像"
    echo "  2. Python 版本过低 - 需要 3.8+"
    exit 1
fi

echo
echo "✅ 依赖安装完成"
echo

# 创建必要目录
echo "[4/4] 初始化项目结构..."
mkdir -p data/raw
mkdir -p index
echo "✅ 目录结构已创建"

echo
echo "========================================"
echo "  🎉 安装完成！"
echo "========================================"
echo
echo "下一步："
echo "  1. 将文档放入 data/raw/ 目录"
echo "     支持格式：.md, .txt, .json, .ast"
echo
echo "  2. 运行入库脚本："
echo "     .venv/bin/python scripts/ingest.py --full"
echo
echo "  3. 启动 Web 界面："
echo "     .venv/bin/streamlit run scripts/app.py"
echo
echo "  4. 或使用命令行查询："
echo "     .venv/bin/python scripts/query.py '你的问题'"
echo
echo "提示："
echo "  - 首次运行会自动下载嵌入模型 (~90MB)"
echo "  - 国内网络设置 HuggingFace 镜像："
echo "    export HF_ENDPOINT=https://hf-mirror.com"
echo
