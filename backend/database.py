"""
YOLO-SmartHome 数据库连接模块
基于 SQLAlchemy 提供数据库引擎、会话工厂及依赖注入
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from config import get_database_url

engine = None
SessionLocal = None
Base = declarative_base()

def init_engine():
    global engine, SessionLocal
    url = get_database_url()
    if not url:
        return False
    
    engine = create_engine(
        url,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=False
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return True


def get_db():
    if SessionLocal is None:
        init_engine()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    import models  # noqa: F401
    if engine is None:
        if not init_engine():
            print("⚠️ 数据库连接尚未配置，跳过自动建表。")
            return False
            
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ 数据库表已自动创建/同步")
        return True
    except Exception as e:
        print(f"❌ 数据库建表失败，请检查配置: {e}")
        return False
