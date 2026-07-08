"""
会话数据管理系统 - FastAPI 入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.database import init_db
from api.sessions import router as sessions_router
from api.upload import router as upload_router
from api.reports import router as reports_router

app = FastAPI(
    title="会话数据管理系统",
    description="qeubee客服会话数据管理、分析与AI总结",
    version="2.0.0",
)

# 跨域配置（允许Vue前端访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境改为具体前端地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(sessions_router)
app.include_router(upload_router)
app.include_router(reports_router)


@app.on_event("startup")
def startup():
    """启动时建表"""
    init_db()
    print("✅ 数据库初始化完成")
    print("📊 访问 http://localhost:8000/docs 查看 API 文档")


@app.get("/")
def root():
    return {
        "message": "会话数据管理系统 API v2.0",
        "docs": "/docs",
        "status": "running"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
