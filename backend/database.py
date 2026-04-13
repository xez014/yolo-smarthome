"""
YOLO-SmartHome 数据库连接模块
基于 SQLAlchemy 提供数据库引擎、会话工厂及依赖注入
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from config import DATABASE_URL

# 创建数据库引擎
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,         # 自动检测断开的连接
    pool_recycle=3600,          # 每小时回收连接
    echo=False                  # 生产环境关闭 SQL 日志
)

# 会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ORM 基类
Base = declarative_base()


def get_db():
    """
    FastAPI 依赖注入：获取数据库会话
    使用方式: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    初始化数据库：自动创建所有 ORM 模型对应的表
    在 FastAPI 启动事件中调用
    """
    import models  # noqa: F401 — 确保 ORM 模型被注册
    Base.metadata.create_all(bind=engine)
    print("✅ 数据库表已自动创建/同步")
