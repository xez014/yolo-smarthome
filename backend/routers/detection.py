"""
YOLO-SmartHome 检测记录查询路由
提供物品检索、历史记录查询等接口
"""
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from database import get_db
from models import DetectionRecord, ObjectLastSeen
from schemas import DetectionRecordOut, ObjectSearchResult, PaginatedResponse, ClassItem
import config

router = APIRouter(prefix="/api/detection", tags=["物品检测"])


@router.get("/classes", response_model=List[ClassItem])
async def get_classes():
    """获取所有 20 类物品列表"""
    return [
        ClassItem(
            class_id=i,
            class_name=name,
            class_name_zh=config.CLASS_NAMES_ZH.get(name, name)
        )
        for i, name in enumerate(config.CLASS_NAMES)
    ]


@router.get("/search", response_model=Optional[ObjectSearchResult])
async def search_object(
    object_class: str = Query(..., description="物品类别英文名称，如 laptop, chair"),
    db: Session = Depends(get_db)
):
    """
    按类别查询物品最后出现的位置和时间
    核心功能："我的笔记本电脑最后出现在哪里？"
    """
    result = db.query(ObjectLastSeen).filter_by(object_class=object_class).first()
    if not result:
        return None

    return ObjectSearchResult(
        object_class=result.object_class,
        class_id=result.class_id,
        class_name_zh=config.CLASS_NAMES_ZH.get(result.object_class, result.object_class),
        last_bbox_x=result.last_bbox_x,
        last_bbox_y=result.last_bbox_y,
        last_bbox_w=result.last_bbox_w,
        last_bbox_h=result.last_bbox_h,
        last_snapshot_path=result.last_snapshot_path,
        last_seen_at=result.last_seen_at,
        total_count=result.total_count,
        camera_id=result.camera_id,
    )


@router.get("/last-seen", response_model=List[ObjectSearchResult])
async def get_all_last_seen(db: Session = Depends(get_db)):
    """获取所有物品的最后出现位置汇总"""
    results = db.query(ObjectLastSeen).order_by(desc(ObjectLastSeen.last_seen_at)).all()
    return [
        ObjectSearchResult(
            object_class=r.object_class,
            class_id=r.class_id,
            class_name_zh=config.CLASS_NAMES_ZH.get(r.object_class, r.object_class),
            last_bbox_x=r.last_bbox_x,
            last_bbox_y=r.last_bbox_y,
            last_bbox_w=r.last_bbox_w,
            last_bbox_h=r.last_bbox_h,
            last_snapshot_path=r.last_snapshot_path,
            last_seen_at=r.last_seen_at,
            total_count=r.total_count,
            camera_id=r.camera_id,
        )
        for r in results
    ]


@router.get("/history", response_model=PaginatedResponse)
async def get_history(
    object_class: Optional[str] = Query(None, description="物品类别筛选"),
    start_time: Optional[datetime] = Query(None, description="起始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    查询历史检测记录（分页）
    支持按物品类别和时间范围筛选
    """
    query = db.query(DetectionRecord)

    if object_class:
        query = query.filter(DetectionRecord.object_class == object_class)
    if start_time:
        query = query.filter(DetectionRecord.detected_at >= start_time)
    if end_time:
        query = query.filter(DetectionRecord.detected_at <= end_time)

    total = query.count()

    items = (
        query.order_by(desc(DetectionRecord.detected_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return PaginatedResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[DetectionRecordOut.model_validate(item) for item in items]
    )
