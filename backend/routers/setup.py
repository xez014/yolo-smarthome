from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import create_engine

from config import save_db_config, get_database_url
import database

router = APIRouter(prefix="/api/system", tags=["系统配置"])

class DBConfig(BaseModel):
    host: str
    port: str
    user: str
    password: str
    dbname: str

@router.get("/status")
async def system_status():
    """检查系统是否已经成功初始化数据库"""
    if database.engine is None:
        database.init_engine()
    
    is_setup = (database.engine is not None)
    return {"is_setup": is_setup}

@router.post("/test-db")
async def test_db_connection(cfg: DBConfig):
    """仅测试传入的数据库连通性"""
    url = f"mysql+pymysql://{cfg.user}:{cfg.password}@{cfg.host}:{cfg.port}/{cfg.dbname}?charset=utf8mb4"
    try:
        tmp_engine = create_engine(url)
        with tmp_engine.connect() as conn:
            pass
        return {"status": "ok", "message": "连接成功"}
    except Exception as e:
        return {"status": "error", "message": f"连接失败: {str(e)}"}

@router.post("/init-db")
async def initialize_system(cfg: DBConfig):
    """保存凭据并创建数据表"""
    try:
        save_db_config(cfg.host, cfg.port, cfg.user, cfg.password, cfg.dbname)
        database.engine = None
        database.SessionLocal = None
        
        success = database.init_db()
        if success:
            return {"status": "ok", "message": "系统初始化完成"}
        else:
            return {"status": "error", "message": "建表失败，请检查账号权限"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
