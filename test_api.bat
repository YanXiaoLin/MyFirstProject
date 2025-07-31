@echo off
echo ============================================================
echo iwhereGIS 网格数据引擎 HTTP API 测试
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

REM 运行测试
echo.
echo 正在运行API测试...
echo ============================================================
python test_api.py

echo.
echo 测试完成！
pause 