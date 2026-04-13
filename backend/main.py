"""
YOLO-SmartHome FastAPI 后端主入口
提供实时视频推流、物品检索、数据统计等 RESTful API
"""
import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# 确保 backend/ 目录在 Python 路径中
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import CORS_ORIGINS, SNAPSHOTS_DIR
from database import init_db
from routers import video, detection, stats


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理：启动时初始化数据库，关闭时清理资源"""
    # === 启动 ===
    print("🚀 YOLO-SmartHome 后端服务启动中...")
    init_db()
    print("✅ 服务就绪！")
    yield
    # === 关闭 ===
    from detection_engine import engine_instance
    if engine_instance.is_running:
        engine_instance.stop()
    print("👋 服务已关闭")


app = FastAPI(
    title="YOLO-SmartHome API",
    description="智能家居视觉感知与检索系统 — 后端 API 服务",
    version="1.0.0",
    lifespan=lifespan,
)

# === CORS 中间件 ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === 静态文件：快照截帧 ===
SNAPSHOTS_DIR.mkdir(exist_ok=True)
app.mount("/snapshots", StaticFiles(directory=str(SNAPSHOTS_DIR)), name="snapshots")

# === 注册路由 ===
app.include_router(video.router)
app.include_router(detection.router)
app.include_router(stats.router)


@app.get("/", tags=["系统"])
async def root():
    """API 根路径 — 系统信息"""
    return {
        "name": "YOLO-SmartHome API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running",
    }


@app.get("/api/health", tags=["系统"])
async def health_check():
    """健康检查接口"""
    from detection_engine import engine_instance
    return {
        "status": "healthy",
        "engine": engine_instance.get_status(),
    }
