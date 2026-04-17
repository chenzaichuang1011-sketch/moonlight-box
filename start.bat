@echo off
chcp 65001 >nul 2>&1
title 月光宝盒 - 后端服务

echo ========================================
echo   月光宝盒 - 启动后端服务
echo ========================================
echo.

cd /d "%~dp0backend"

:: 优先使用本地 venv
if exist "venv\Scripts\python.exe" (
    set PYTHON="%~dp0backend\venv\Scripts\python.exe"
) else (
    set PYTHON=python
)

%PYTHON% -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo ❌ 依赖未安装，请先运行 install.bat
    pause
    exit /b 1
)

echo   📡 API:   http://127.0.0.1:8001
echo   📖 文档:  http://127.0.0.1:8001/docs
echo   🌐 前端:  http://127.0.0.1:8001
echo.
echo   按 Ctrl+C 停止服务
echo.

%PYTHON% -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
pause
