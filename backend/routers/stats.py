"""
YOLO-SmartHome 统计数据路由
提供 ECharts 图表所需的统计数据接口
"""
from datetime import datetime, date, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from database import get_db
from models import DetectionRecord, DetectionStat, ObjectLastSeen
from schemas import StatOverview, FrequencyItem, TimelineItem
from detection_engine import engine_instance
from auth import get_current_user
import config

router = APIRouter(prefix="/api/stats", tags=["统计数据"], dependencies=[Depends(get_current_user)])


@router.get("/overview", response_model=StatOverview)
async def get_overview(db: Session = Depends(get_db)):
    """
    获取首页统计概览
    - 今日累计检测数
    - 活跃物品种类数
    - 当前 FPS
    - 当前画面物品数
    """
    today = date.today()

    # 今日总检测数
    today_total = db.query(func.sum(DetectionStat.detection_count)).filter(
        DetectionStat.stat_date == today
    ).scalar() or 0

    # 活跃种类数（有检测记录的类别数）
    active_classes = db.query(func.count(func.distinct(DetectionStat.object_class))).filter(
        DetectionStat.stat_date == today
    ).scalar() or 0

    # 实时数据来自引擎
    status = engine_instance.get_status()

    return StatOverview(
        today_total=int(today_total),
        active_classes=int(active_classes),
        current_fps=status["fps"],
        current_objects=status["current_objects"],
    )


@router.get("/frequency", response_model=List[FrequencyItem])
async def get_frequency(
    days: int = Query(7, ge=1, le=30, description="统计最近N天"),
    limit: int = Query(20, ge=1, le=20, description="返回前N类"),
    db: Session = Depends(get_db)
):
    """
    各类物品出现频次排行（用于柱状图/饼图）
    """
    start_date = date.today() - timedelta(days=days)

    results = (
        db.query(
            DetectionStat.object_class,
            func.sum(DetectionStat.detection_count).label("total")
        )
        .filter(DetectionStat.stat_date >= start_date)
        .group_by(DetectionStat.object_class)
        .order_by(desc("total"))
        .limit(limit)
        .all()
    )

    return [
        FrequencyItem(
            object_class=r.object_class,
            class_name_zh=config.CLASS_NAMES_ZH.get(r.object_class, r.object_class),
            count=int(r.total)
        )
        for r in results
    ]


@router.get("/timeline", response_model=List[TimelineItem])
async def get_timeline(
    target_date: Optional[date] = Query(None, description="目标日期，默认今天"),
    db: Session = Depends(get_db)
):
    """
    按小时统计时间轴数据（用于折线图）
    """
    if target_date is None:
        target_date = date.today()

    results = (
        db.query(
            DetectionStat.stat_hour,
            func.sum(DetectionStat.detection_count).label("total")
        )
        .filter(DetectionStat.stat_date == target_date)
        .filter(DetectionStat.stat_hour.isnot(None))
        .group_by(DetectionStat.stat_hour)
        .order_by(DetectionStat.stat_hour)
        .all()
    )

    # 补全 24 小时（缺失的小时数填 0）
    hour_data = {r.stat_hour: int(r.total) for r in results}
    timeline = [
        TimelineItem(hour=h, count=hour_data.get(h, 0))
        for h in range(24)
    ]

    return timeline


@router.get("/realtime")
async def get_realtime():
    """
    获取实时检测统计（当前帧的检测结果汇总）
    """
    detections = engine_instance.current_detections
    class_counts = {}
    for det in detections:
        name = det.get("class_name_zh", det.get("class_name", "unknown"))
        class_counts[name] = class_counts.get(name, 0) + 1

    return {
        "fps": round(engine_instance.current_fps, 1),
        "total_objects": len(detections),
        "class_counts": class_counts,
        "is_running": engine_instance.is_running,
    }
