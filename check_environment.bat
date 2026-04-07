@echo off
echo ========================================
echo 环境检查
echo ========================================
echo.

echo [1/6] 检查 Python...
python --version
if %errorlevel% neq 0 (
    echo ❌ Python 未安装
    goto :error
) else (
    echo ✓ Python 已安装
)
echo.

echo [2/6] 检查 Node.js...
node --version
if %errorlevel% neq 0 (
    echo ❌ Node.js 未安装
    goto :error
) else (
    echo ✓ Node.js 已安装
)
echo.

echo [3/6] 检查 npm...
npm --version
if %errorlevel% neq 0 (
    echo ❌ npm 未安装
    goto :error
) else (
    echo ✓ npm 已安装
)
echo.

echo [4/6] 检查后端依赖...
cd backend
pip show fastapi >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 后端依赖未安装，请运行 install_backend_deps.bat
    cd ..
    goto :error
) else (
    echo ✓ 后端依赖已安装
)
cd ..
echo.

echo [5/6] 检查前端依赖...
if exist "frontend\node_modules\vue" (
    echo ✓ 前端依赖已安装
) else (
    echo ❌ 前端依赖未安装，请运行 install_frontend_deps.bat
    goto :error
)
echo.

echo [6/6] 检查配置文件...
if exist "backend\.env" (
    echo ✓ 后端配置文件存在
) else (
    echo ❌ 后端配置文件不存在，请复制 .env.example 为 .env
    goto :error
)
echo.

echo ========================================
echo ✓ 环境检查通过！
echo ========================================
echo.
echo 可以开始启动服务：
echo 1. 双击 start_backend.bat 启动后端
echo 2. 双击 start_frontend.bat 启动前端
echo.
goto :end

:error
echo.
echo ========================================
echo ❌ 环境检查失败
echo ========================================
echo 请根据上述提示修复问题后重试
echo.

:end
pause
