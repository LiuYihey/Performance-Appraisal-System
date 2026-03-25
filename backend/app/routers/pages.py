from fastapi import APIRouter, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

router = APIRouter()

# 前端静态文件目录
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIST = os.path.join(os.path.dirname(APP_DIR), "frontend", "dist")


@router.get("/")
async def serve_index():
    """返回前端入口页面"""
    index_path = os.path.join(FRONTEND_DIST, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    # 开发阶段返回简单的欢迎页
    return FileResponse(os.path.join(APP_DIR, "welcome.html"))


@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "绩效管理系统"}
