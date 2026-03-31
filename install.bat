@echo off
chcp 65001 >nul
echo ========================================
echo   RAG UE Toolkit - 一键安装
echo ========================================
echo.

REM 检查 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Python，请先安装 Python 3.8+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/4] 检测到 Python:
python --version
echo.

REM 创建虚拟环境
if not exist .venv (
    echo [2/4] 创建虚拟环境...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [错误] 创建虚拟环境失败
        pause
        exit /b 1
    )
    echo ✅ 虚拟环境已创建
) else (
    echo [2/4] 虚拟环境已存在，跳过创建
)
echo.

REM 激活虚拟环境并安装依赖
echo [3/4] 安装 Python 依赖包...
echo 提示：首次安装需下载 ~1.3GB（包含 PyTorch）
echo       国内网络较慢时，可设置镜像：
echo       set PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/
echo.

call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo [错误] 依赖安装失败！
    echo 常见原因：
    echo   1. 网络问题 - 尝试设置 pip 镜像
    echo   2. Python 版本过低 - 需要 3.8+
    pause
    exit /b 1
)

echo.
echo ✅ 依赖安装完成
echo.

REM 创建必要目录
echo [4/4] 初始化项目结构...
if not exist data\raw (
    mkdir data\raw
    echo ✅ 创建 data\raw 目录
)
if not exist index (
    mkdir index
    echo ✅ 创建 index 目录
)

echo.
echo ========================================
echo   🎉 安装完成！
echo ========================================
echo.
echo 下一步：
echo   1. 将文档放入 data\raw\ 目录
echo      支持格式：.md, .txt, .json, .ast
echo.
echo   2. 运行入库脚本：
echo      .venv\Scripts\python scripts\ingest.py --full
echo.
echo   3. 启动 Web 界面：
echo      .venv\Scripts\streamlit run scripts\app.py
echo.
echo   4. 或使用命令行查询：
echo      .venv\Scripts\python scripts\query.py "你的问题"
echo.
echo 提示：
echo   - 首次运行会自动下载嵌入模型 (~90MB)
echo   - 国内网络设置 HuggingFace 镜像：
echo     set HF_ENDPOINT=https://hf-mirror.com
echo.
pause
