"""
YOLO-SmartHome 认证鉴权模块
单管理员模式 — 密码通过环境变量 ADMIN_PASSWORD 配置
"""
import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from jose import JWTError, jwt

# === 配置 ===
SECRET_KEY = os.getenv("JWT_SECRET", "yolo-smarthome-secret-key-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# === Security 方案 ===
security = HTTPBearer(auto_error=False)

router = APIRouter(prefix="/api/auth", tags=["认证"])


# === 数据模型 ===
class LoginRequest(BaseModel):
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # 秒


# === Token 工具函数 ===
def create_access_token(expires_delta: Optional[timedelta] = None) -> str:
    """签发 JWT Token"""
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS))
    to_encode = {"sub": "admin", "exp": expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> bool:
    """验证 JWT Token 有效性"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub") == "admin"
    except JWTError:
        return False


# === FastAPI 依赖注入 ===
async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
):
    """鉴权依赖 — 从 Authorization 头提取并校验 Token"""
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_token(credentials.credentials):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证令牌无效或已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return "admin"


def verify_ws_token(token: Optional[str]) -> bool:
    """WebSocket 鉴权 — 从 query 参数校验 Token"""
    if not token:
        return False
    return verify_token(token)


# === 路由 ===
@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    """管理员登录接口"""
    if req.password != ADMIN_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="密码错误",
        )

    token = create_access_token()
    return TokenResponse(
        access_token=token,
        expires_in=ACCESS_TOKEN_EXPIRE_HOURS * 3600,
    )


@router.get("/verify")
async def verify(user: str = Depends(get_current_user)):
    """验证当前 Token 是否有效"""
    return {"status": "ok", "user": user}
