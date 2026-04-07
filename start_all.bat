@echo off
echo ========================================
echo 烘焙配方管理系统 - 一键启动
echo ========================================
echo.

echo 正在启动后端服务...
start "后端服务" cmd /k "python backend/main.py"
timeout /t 3 /nobreak >nul

echo 正在启动前端服务...
start "前端服务" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================
echo 服务启动中...
echo ========================================
echo.
echo 后端服务: http://localhost:8000
echo API文档: http://localhost:8000/docs
echo 前端服务: http://localhost:3000
echo.
echo 请等待服务完全启动后访问
echo 关闭此窗口不会停止服务
echo.
pause
