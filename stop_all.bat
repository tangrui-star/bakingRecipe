@echo off
echo ========================================
echo 停止所有服务
echo ========================================
echo.

echo 正在停止后端服务...
taskkill /FI "WINDOWTITLE eq 后端服务*" /F >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ 后端服务已停止
) else (
    echo - 后端服务未运行
)

echo 正在停止前端服务...
taskkill /FI "WINDOWTITLE eq 前端服务*" /F >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ 前端服务已停止
) else (
    echo - 前端服务未运行
)

echo.
echo 所有服务已停止
pause
