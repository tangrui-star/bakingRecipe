from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import sys
import os

# 添加backend目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from routers import recipes, ingredients, categories, shops, auth, blacklist, screening
from config import settings

app = FastAPI(
    title="烘焙配方管理系统 API",
    version="2.0.0",
    description="包含用户认证、配方管理等功能"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建上传目录
os.makedirs(settings.upload_dir, exist_ok=True)

# 静态文件服务（用于头像等）
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

# 注册路由
app.include_router(auth.router, prefix="/api/auth", tags=["用户认证"])
app.include_router(shops.router, prefix="/api/shops", tags=["店铺"])
app.include_router(categories.router, prefix="/api/categories", tags=["品类"])
app.include_router(ingredients.router, prefix="/api/ingredients", tags=["原料"])
app.include_router(recipes.router, prefix="/api/recipes", tags=["配方"])
app.include_router(blacklist.router, tags=["黑名单管理"])
app.include_router(screening.router, tags=["订单检查"])

@app.get("/")
def root():
    return {
        "message": "烘焙配方管理系统 API",
        "version": "2.0.0",
        "features": ["用户认证", "配方管理", "版本控制", "配方计算", "热量计算", "黑名单管理", "订单检查"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.api_host, port=settings.api_port)
