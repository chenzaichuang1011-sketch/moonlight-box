@echo off
chcp 65001 >nul 2>&1
title 月光宝盒 - 安装依赖

echo ========================================
echo   月光宝盒 - 安装依赖
echo ========================================
echo.

:: 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到 Python，请先安装 Python 3.11+
    echo    下载地址：https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/3] 创建虚拟环境...
cd /d "%~dp0backend"
python -m venv venv
if errorlevel 1 (
    echo ❌ 虚拟环境创建失败
    pause
    exit /b 1
)

echo [2/3] 激活虚拟环境...
call venv\Scripts\activate.bat

echo [3/3] 安装依赖...
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
if errorlevel 1 (
    echo ❌ 依赖安装失败，请检查网络后重试
    pause
    exit /b 1
)

echo.
echo ✅ 安装完成！现在可以运行 start.bat 启动服务
pause
