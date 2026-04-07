@echo off
echo ========================================
echo 安装用户认证依赖
echo ========================================
echo.

cd backend

echo 正在安装依赖...
pip install python-jose[cryptography]==3.3.0
pip install passlib[bcrypt]==1.7.4
pip install captcha==0.5.0
pip install pillow==10.2.0

echo.
echo ========================================
echo 依赖安装完成！
echo ========================================
pause
