@echo off
echo ============================================================
echo iwhereGIS 网格数据引擎 HTTP API 服务器
echo ============================================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.7+
    pause
    exit /b 1
)

REM 安装依赖
echo 检查并安装依赖...
pip install -r requirements.txt

REM 启动服务器
echo.
echo 正在启动API服务器...
echo 服务器地址: http://localhost:5000
echo 按 Ctrl+C 停止服务器
echo ============================================================
python api_server.py

pause 