@echo off
chcp 65001 >nul
title iwhereGIS 网格数据引擎可视化系统

echo ================================================
echo iwhereGIS 网格数据引擎可视化系统
echo ================================================

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ✗ 错误: 未找到Python，请先安装Python
    pause
    exit /b 1
)

echo ✓ Python 已安装

REM 检查依赖
echo 检查依赖包...
pip show flask >nul 2>&1
if errorlevel 1 (
    echo 安装依赖包...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ✗ 依赖安装失败
        pause
        exit /b 1
    )
)

echo ✓ 依赖检查完成

REM 检查静态文件
if not exist "static\index.html" (
    echo ✗ 错误: 找不到 static\index.html 文件
    pause
    exit /b 1
)

echo ✓ 静态文件检查完成

echo.
echo 正在启动可视化系统...
echo 请稍候...

REM 启动可视化系统
python start_visualization.py

echo.
echo 系统已停止
pause 