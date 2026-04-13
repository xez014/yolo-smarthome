"""
YOLO-SmartHome ORM 模型定义
定义三张核心数据表：检测记录、物品最后位置、统计汇总
"""
from datetime import datetime

from sqlalchemy import Column, Integer, BigInteger, String, Float, DateTime, Date, UniqueConstraint, Index
from database import Base


class DetectionRecord(Base):
    """物品检测记录表 — 存储每次检测到的物品信息"""
    __tablename__ = "detection_records"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    object_class = Column(String(50), nullable=False, index=True, comment="物品类别名称")
    class_id = Column(Integer, nullable=False, comment="类别ID (0-19)")
    confidence = Column(Float, nullable=False, comment="检测置信度")
    bbox_x = Column(Float, nullable=False, comment="边界框中心X (归一化)")
    bbox_y = Column(Float, nullable=False, comment="边界框中心Y (归一化)")
    bbox_w = Column(Float, nullable=False, comment="边界框宽度 (归一化)")
    bbox_h = Column(Float, nullable=False, comment="边界框高度 (归一化)")
    track_id = Column(Integer, nullable=True, comment="ByteTrack 追踪ID")
    snapshot_path = Column(String(255), nullable=True, comment="截帧快照文件路径")
    detected_at = Column(DateTime, nullable=False, default=datetime.now, comment="检测时间")
    camera_id = Column(String(50), default="cam_01", comment="摄像头标识")

    __table_args__ = (
        Index("idx_class_time", "object_class", "detected_at"),
    )


class ObjectLastSeen(Base):
    """物品最后出现位置表 — 维护每类物品的最新位置，支持快速检索"""
    __tablename__ = "object_last_seen"

    id = Column(Integer, primary_key=True, autoincrement=True)
    object_class = Column(String(50), nullable=False, unique=True, comment="物品类别")
    class_id = Column(Integer, nullable=False)
    last_bbox_x = Column(Float, nullable=True)
    last_bbox_y = Column(Float, nullable=True)
    last_bbox_w = Column(Float, nullable=True)
    last_bbox_h = Column(Float, nullable=True)
    last_snapshot_path = Column(String(255), nullable=True, comment="最后一次出现的快照")
    last_seen_at = Column(DateTime, nullable=False, comment="最后出现时间")
    total_count = Column(Integer, default=0, comment="累计出现次数")
    camera_id = Column(String(50), default="cam_01")

    __table_args__ = (
        Index("idx_last_seen_at", "last_seen_at"),
    )


class DetectionStat(Base):
    """统计概要表 — 按小时/天汇总检测统计"""
    __tablename__ = "detection_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stat_date = Column(Date, nullable=False, comment="统计日期")
    stat_hour = Column(Integer, nullable=True, comment="统计小时 (0-23), NULL表示全天")
    object_class = Column(String(50), nullable=False)
    detection_count = Column(Integer, default=0, comment="检测次数")

    __table_args__ = (
        UniqueConstraint("stat_date", "stat_hour", "object_class", name="uk_stat"),
    )
