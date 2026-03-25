from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, plans, evaluation, pages, employees, hr, export, admin
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

app = FastAPI(
    title="绩效管理系统",
    version="0.1.0",
    description="企业微信自动化绩效管理平台",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router)
app.include_router(plans.router)
app.include_router(evaluation.router)
app.include_router(hr.router)
app.include_router(employees.router)
app.include_router(export.router)
app.include_router(admin.router)
app.include_router(pages.router)


@app.on_event("startup")
def startup():
    """启动时自动建表"""
    from app.database import engine
    from app.models import Base
    Base.metadata.create_all(bind=engine)
    print("[OK] Database tables created/checked")


@app.get("/health")
def health():
    return {"status": "ok", "service": "绩效管理系统"}


import socket

def find_free_port(start: int = 8000, max_tries: int = 10) -> int:
    for port in range(start, start + max_tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("0.0.0.0", port))
                return port
            except OSError:
                continue
    raise RuntimeError(f"端口 {start}-{start + max_tries - 1} 全部被占用")


if __name__ == "__main__":
    import uvicorn
    port = find_free_port()
    print(f"[OK] 使用端口: {port}")
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
