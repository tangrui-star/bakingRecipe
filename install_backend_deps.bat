@echo off
echo ========================================
echo 安装后端依赖
echo ========================================
echo.

cd backend
echo 正在安装后端依赖...
pip install -r requirements.txt

echo.
echo 后端依赖安装完成！
pause
