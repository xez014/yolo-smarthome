"""
YOLO-SmartHome Pydantic Schema 定义
用于 FastAPI 请求/响应的数据验证与序列化
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


# === 检测记录相关 ===

class DetectionRecordOut(BaseModel):
    """检测记录响应模型"""
    id: int
    object_class: str
    class_id: int
    confidence: float
    bbox_x: float
    bbox_y: float
    bbox_w: float
    bbox_h: float
    track_id: Optional[int] = None
    snapshot_path: Optional[str] = None
    detected_at: datetime
    camera_id: str = "cam_01"

    class Config:
        from_attributes = True


class ObjectSearchResult(BaseModel):
    """物品检索结果模型"""
    object_class: str
    class_id: int
    class_name_zh: str = ""
    last_bbox_x: Optional[float] = None
    last_bbox_y: Optional[float] = None
    last_bbox_w: Optional[float] = None
    last_bbox_h: Optional[float] = None
    last_snapshot_path: Optional[str] = None
    last_seen_at: Optional[datetime] = None
    total_count: int = 0
    camera_id: str = "cam_01"

    class Config:
        from_attributes = True


class DetectionHistoryQuery(BaseModel):
    """检测历史查询参数"""
    object_class: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    page: int = 1
    page_size: int = 20


class PaginatedResponse(BaseModel):
    """分页响应通用模型"""
    total: int
    page: int
    page_size: int
    items: List[DetectionRecordOut]


# === 统计数据相关 ===

class StatOverview(BaseModel):
    """首页统计概览"""
    today_total: int = 0
    active_classes: int = 0
    current_fps: float = 0.0
    current_objects: int = 0


class FrequencyItem(BaseModel):
    """物品频次统计项"""
    object_class: str
    class_name_zh: str
    count: int


class TimelineItem(BaseModel):
    """时间轴统计项"""
    hour: int
    count: int


class ClassItem(BaseModel):
    """物品类别信息"""
    class_id: int
    class_name: str
    class_name_zh: str


# === 实时检测数据（WebSocket 推送） ===

class DetectionBox(BaseModel):
    """单个检测框"""
    class_id: int
    class_name: str
    class_name_zh: str
    confidence: float
    x1: float
    y1: float
    x2: float
    y2: float
    track_id: Optional[int] = None


class RealtimeFrame(BaseModel):
    """实时帧数据（WebSocket 推送）"""
    fps: float
    frame_count: int
    timestamp: str
    detections: List[DetectionBox]
