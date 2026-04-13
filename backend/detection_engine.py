"""
YOLO-SmartHome 检测推理引擎
核心模块：YOLO 模型推理 + 多目标追踪 + 数据库持久化 + 快照保存
"""
import cv2
import time
import threading
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict
from collections import defaultdict

from ultralytics import YOLO

import config
import database
from models import DetectionRecord, ObjectLastSeen, DetectionStat


class DetectionEngine:
    """YOLO 目标检测 + 追踪引擎（单例模式）"""

    _instance: Optional["DetectionEngine"] = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        # 模型 & 摄像头
        self.model: Optional[YOLO] = None
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_running = False
        self._source = None          # 当前实际使用的视频源
        self._source_type = "none"   # webcam / video / rtsp / none

        # 实时状态
        self.current_frame: Optional[np.ndarray] = None
        self.current_detections: List[Dict] = []
        self.current_fps: float = 0.0
        self.frame_count: int = 0

        # 追踪持久化控制
        self._track_history: Dict[int, int] = defaultdict(int)  # track_id -> 连续出现帧数
        self._last_snapshot_time: float = 0
        self._last_db_write_time: float = 0

        # 推理线程
        self._thread: Optional[threading.Thread] = None
        self._frame_lock = threading.Lock()

        # 加载模型
        self._load_model()

    def _load_model(self):
        """加载 YOLO 模型权重"""
        weights = config.WEIGHTS_PATH
        if not Path(weights).exists():
            print(f"⚠️ 模型权重文件不存在: {weights}")
            print("请确认 best.pt 已放置在正确位置")
            return

        print(f"正在加载 YOLO 模型: {weights}")
        self.model = YOLO(weights)
        print("✅ YOLO 模型加载完成")

    def start(self, source=None):
        """启动摄像头推理"""
        if self.is_running:
            return {"status": "already_running"}

        if self.model is None:
            return {"status": "error", "message": "模型未加载"}

        src = source if source is not None else config.CAMERA_SOURCE
        
        # 自动清洗 Windows "复制文件路径" 时自带的隐藏双引号或单引号
        if isinstance(src, str):
            src = src.strip('"\'')
            
        self._source = src

        # 判断视频源类型
        if isinstance(src, int):
            self._source_type = "webcam"
        elif isinstance(src, str) and (src.startswith("rtsp://") or src.startswith("rtmp://") or src.startswith("http")):
            self._source_type = "rtsp"
        else:
            self._source_type = "video"

        self.cap = cv2.VideoCapture(src)

        if not self.cap.isOpened():
            self._source_type = "none"
            return {"status": "error", "message": f"无法打开摄像头/视频源: {src}"}

        self.is_running = True
        self.frame_count = 0
        self._track_history.clear()
        self._thread = threading.Thread(target=self._inference_loop, daemon=True)
        self._thread.start()
        source_label = {"webcam": "本机摄像头", "video": "视频文件", "rtsp": "网络流"}.get(self._source_type, str(src))
        print(f"✅ 推理已启动，视频源: {source_label} ({src})")
        return {"status": "started", "source_type": self._source_type}

    def stop(self):
        """停止推理"""
        self.is_running = False
        if self._thread:
            self._thread.join(timeout=5)
        if self.cap:
            self.cap.release()
            self.cap = None
        self.current_frame = None
        self.current_detections = []
        self._source = None
        self._source_type = "none"
        print("⏹️ 推理已停止")
        return {"status": "stopped"}

    def _inference_loop(self):
        """推理主循环（在后台线程中运行）"""
        fps_timer = time.time()
        fps_counter = 0

        while self.is_running and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                # 视频文件播放完毕，自动循环播放
                if self._source_type == "video":
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                break

            self.frame_count += 1
            fps_counter += 1

            # 计算 FPS（每秒更新一次）
            elapsed = time.time() - fps_timer
            if elapsed >= 1.0:
                self.current_fps = fps_counter / elapsed
                fps_counter = 0
                fps_timer = time.time()

            # YOLO 推理 + 追踪
            results = self.model.track(
                frame,
                conf=config.CONFIDENCE_THRESHOLD,
                iou=config.IOU_THRESHOLD,
                imgsz=config.INPUT_SIZE,
                tracker=config.TRACKER_TYPE,
                persist=True,
                verbose=False
            )

            # 解析检测结果
            detections = self._parse_results(results, frame)

            # 在帧上绘制检测框
            annotated_frame = self._draw_detections(frame, detections)

            with self._frame_lock:
                self.current_frame = annotated_frame
                self.current_detections = detections

            # 持久化：定时保存到数据库 & 快照 (传入被绘制好边框的 annotated_frame 修复快照无线框的问题)
            self._persist_detections(detections, annotated_frame)

        self.is_running = False

    def _parse_results(self, results, frame) -> List[Dict]:
        """解析 YOLO 推理结果为结构化数据"""
        detections = []
        if not results or len(results) == 0:
            return detections

        result = results[0]
        h, w = frame.shape[:2]

        if result.boxes is None or len(result.boxes) == 0:
            return detections

        boxes = result.boxes
        for i in range(len(boxes)):
            cls_id = int(boxes.cls[i])
            conf = float(boxes.conf[i])

            # xyxy 像素坐标
            x1, y1, x2, y2 = boxes.xyxy[i].tolist()

            # 归一化中心坐标 + 宽高
            cx = ((x1 + x2) / 2) / w
            cy = ((y1 + y2) / 2) / h
            bw = (x2 - x1) / w
            bh = (y2 - y1) / h

            # 追踪 ID
            track_id = None
            if boxes.id is not None:
                track_id = int(boxes.id[i])

            class_name = config.CLASS_NAMES[cls_id] if cls_id < len(config.CLASS_NAMES) else f"class_{cls_id}"

            detections.append({
                "class_id": cls_id,
                "class_name": class_name,
                "class_name_zh": config.CLASS_NAMES_ZH.get(class_name, class_name),
                "confidence": round(conf, 3),
                "x1": round(x1, 1),
                "y1": round(y1, 1),
                "x2": round(x2, 1),
                "y2": round(y2, 1),
                "bbox_x": round(cx, 4),
                "bbox_y": round(cy, 4),
                "bbox_w": round(bw, 4),
                "bbox_h": round(bh, 4),
                "track_id": track_id,
            })

        return detections

    def _draw_detections(self, frame: np.ndarray, detections: List[Dict]) -> np.ndarray:
        """在帧上绘制检测框和标签"""
        annotated = frame.copy()
        colors = [
            (0, 255, 127), (255, 191, 0), (0, 191, 255), (255, 105, 180), (127, 255, 0),
            (255, 215, 0), (0, 255, 255), (255, 69, 0), (138, 43, 226), (50, 205, 50),
            (255, 20, 147), (0, 206, 209), (255, 165, 0), (30, 144, 255), (154, 205, 50),
            (255, 99, 71), (0, 128, 128), (186, 85, 211), (244, 164, 96), (72, 209, 204)
        ]

        for det in detections:
            cls_id = det["class_id"]
            color = colors[cls_id % len(colors)]
            x1, y1, x2, y2 = int(det["x1"]), int(det["y1"]), int(det["x2"]), int(det["y2"])

            # 绘制边界框
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)

            # 标签文本
            label = f"{det['class_name_zh']} {det['confidence']:.0%}"
            if det["track_id"] is not None:
                label = f"[{det['track_id']}] {label}"

            # 标签背景
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(annotated, (x1, y1 - th - 8), (x1 + tw + 4, y1), color, -1)
            cv2.putText(annotated, label, (x1 + 2, y1 - 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)

        # 绘制 FPS
        fps_text = f"FPS: {self.current_fps:.1f}"
        cv2.putText(annotated, fps_text, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2, cv2.LINE_AA)

        return annotated

    def _persist_detections(self, detections: List[Dict], annotated_frame: np.ndarray):
        """将检测结果持久化到数据库（带节流控制和容错机制）"""
        now = time.time()

        if not detections:
            return

        # 更新追踪计数
        active_track_ids = set()
        for det in detections:
            tid = det.get("track_id")
            if tid is not None:
                self._track_history[tid] += 1
                active_track_ids.add(tid)

        # 清理消失的 track_id (引入容错机制，防止25fps视频单帧漏检导致追踪连跳)
        for tid in list(self._track_history.keys()):
            if tid not in active_track_ids:
                # 给予缓冲容错：脱框时扣减 1，直到归零才移除
                self._track_history[tid] -= 1
                if self._track_history[tid] <= 0:
                    del self._track_history[tid]

        # 节流：满足间隔才写入数据库
        if now - self._last_db_write_time < config.DB_WRITE_INTERVAL:
            return

        self._last_db_write_time = now

        # 是否保存快照
        save_snapshot = (now - self._last_snapshot_time >= config.SNAPSHOT_INTERVAL)
        snapshot_path = None

        if save_snapshot:
            self._last_snapshot_time = now
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            snapshot_filename = f"snap_{timestamp_str}.jpg"
            snapshot_full_path = config.SNAPSHOTS_DIR / snapshot_filename
            cv2.imwrite(str(snapshot_full_path), annotated_frame)
            snapshot_path = f"/snapshots/{snapshot_filename}"

        # 写入数据库（在新线程中执行，避免阻塞推理）
        threading.Thread(
            target=self._write_to_db,
            args=(detections, snapshot_path),
            daemon=True
        ).start()

    def _write_to_db(self, detections: List[Dict], snapshot_path: Optional[str]):
        """实际写入数据库的操作"""
        if database.SessionLocal is None:
            return
        db = database.SessionLocal()
        try:
            now = datetime.now()

            class_groups = {}
            for det in detections:
                tid = det.get("track_id")

                # 只持久化追踪稳定的目标
                if tid is not None and self._track_history.get(tid, 0) < config.TRACK_PERSIST_FRAMES:
                    continue

                # 写入检测记录
                record = DetectionRecord(
                    object_class=det["class_name"],
                    class_id=det["class_id"],
                    confidence=det["confidence"],
                    bbox_x=det["bbox_x"],
                    bbox_y=det["bbox_y"],
                    bbox_w=det["bbox_w"],
                    bbox_h=det["bbox_h"],
                    track_id=tid,
                    snapshot_path=snapshot_path,
                    detected_at=now,
                    camera_id=config.CAMERA_ID,
                )
                db.add(record)

                cls_name = det["class_name"]
                if cls_name not in class_groups:
                    class_groups[cls_name] = {"count": 0, "last_det": det}
                class_groups[cls_name]["count"] += 1
                class_groups[cls_name]["last_det"] = det

            for cls_name, group in class_groups.items():
                count = group["count"]
                last_det = group["last_det"]

                # 更新物品最后出现位置
                existing = db.query(ObjectLastSeen).filter_by(object_class=cls_name).first()
                if existing:
                    existing.last_bbox_x = last_det["bbox_x"]
                    existing.last_bbox_y = last_det["bbox_y"]
                    existing.last_bbox_w = last_det["bbox_w"]
                    existing.last_bbox_h = last_det["bbox_h"]
                    existing.last_snapshot_path = snapshot_path or existing.last_snapshot_path
                    existing.last_seen_at = now
                    existing.total_count = (existing.total_count or 0) + count
                else:
                    db.add(ObjectLastSeen(
                        object_class=cls_name,
                        class_id=last_det["class_id"],
                        last_bbox_x=last_det["bbox_x"],
                        last_bbox_y=last_det["bbox_y"],
                        last_bbox_w=last_det["bbox_w"],
                        last_bbox_h=last_det["bbox_h"],
                        last_snapshot_path=snapshot_path,
                        last_seen_at=now,
                        total_count=count,
                        camera_id=config.CAMERA_ID,
                    ))

                # 更新统计表
                stat = db.query(DetectionStat).filter_by(
                    stat_date=now.date(),
                    stat_hour=now.hour,
                    object_class=cls_name
                ).first()

                if stat:
                    stat.detection_count += count
                else:
                    db.add(DetectionStat(
                        stat_date=now.date(),
                        stat_hour=now.hour,
                        object_class=cls_name,
                        detection_count=count
                    ))

            db.commit()
        except Exception as e:
            db.rollback()
            print(f"❌ 数据库写入失败: {e}")
        finally:
            db.close()

    def infer_single_frame(self, raw_bytes: bytes):
        """
        无状态单帧推理接口（供客户端推流模式使用）
        接受原始 JPEG 字节 → YOLO 推理 → 返回 (annotated_jpeg_bytes, detections)
        同时将检测结果持久化到数据库（物品历史 + 统计）
        """
        if self.model is None:
            return None, []

        # 解码图片
        nparr = np.frombuffer(raw_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if frame is None:
            return None, []

        # 推理（不使用 track，避免与主引擎的追踪状态产生干扰）
        results = self.model.predict(
            frame,
            conf=config.CONFIDENCE_THRESHOLD,
            iou=config.IOU_THRESHOLD,
            imgsz=config.INPUT_SIZE,
            verbose=False,
        )

        # 解析结果（不含 track_id）
        detections = self._parse_results(results, frame)

        # 绘制检测框
        annotated = self._draw_detections(frame, detections)

        # 节流持久化：避免每帧都写库（最小间隔 DB_WRITE_INTERVAL 秒）
        if detections:
            self._persist_push_detections(detections, annotated)

        # 编码为 JPEG 字节
        _, buffer = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 75])
        return buffer.tobytes(), detections

    def _persist_push_detections(self, detections: List[Dict], annotated_frame: np.ndarray):
        """
        客户端推流专用持久化入口
        由于无追踪 ID，直接按物品类别写入，节流控制与主引擎共用阈值
        """
        now = time.time()

        # 节流：与主引擎共用写入间隔配置
        if now - self._last_db_write_time < config.DB_WRITE_INTERVAL:
            return
        self._last_db_write_time = now

        # 快照保存
        snapshot_path = None
        if now - self._last_snapshot_time >= config.SNAPSHOT_INTERVAL:
            self._last_snapshot_time = now
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            snap_name = f"push_{ts}.jpg"
            snap_full = config.SNAPSHOTS_DIR / snap_name
            cv2.imwrite(str(snap_full), annotated_frame)
            snapshot_path = f"/snapshots/{snap_name}"

        # 在新线程中写入数据库（不阻塞推理响应）
        threading.Thread(
            target=self._write_push_to_db,
            args=(detections, snapshot_path),
            daemon=True
        ).start()

    def _write_push_to_db(self, detections: List[Dict], snapshot_path: Optional[str]):
        """推流模式写数据库（无追踪 ID，所有检出物品直接落库）"""
        if database.SessionLocal is None:
            return
        db = database.SessionLocal()
        try:
            now = datetime.now()

            class_groups = {}
            for det in detections:
                # 写入基础记录
                record = DetectionRecord(
                    object_class=det["class_name"],
                    class_id=det["class_id"],
                    confidence=det["confidence"],
                    bbox_x=det["bbox_x"],
                    bbox_y=det["bbox_y"],
                    bbox_w=det["bbox_w"],
                    bbox_h=det["bbox_h"],
                    track_id=None,
                    snapshot_path=snapshot_path,
                    detected_at=now,
                    camera_id=config.CAMERA_ID,
                )
                db.add(record)

                cls_name = det["class_name"]
                if cls_name not in class_groups:
                    class_groups[cls_name] = {"count": 0, "last_det": det}
                class_groups[cls_name]["count"] += 1
                class_groups[cls_name]["last_det"] = det

            for cls_name, group in class_groups.items():
                count = group["count"]
                last_det = group["last_det"]

                # 更新最后出现位置
                existing_seen = db.query(ObjectLastSeen).filter_by(object_class=cls_name).first()
                if existing_seen:
                    existing_seen.last_bbox_x = last_det["bbox_x"]
                    existing_seen.last_bbox_y = last_det["bbox_y"]
                    existing_seen.last_bbox_w = last_det["bbox_w"]
                    existing_seen.last_bbox_h = last_det["bbox_h"]
                    existing_seen.last_snapshot_path = snapshot_path or existing_seen.last_snapshot_path
                    existing_seen.last_seen_at = now
                    existing_seen.total_count = (existing_seen.total_count or 0) + count
                else:
                    db.add(ObjectLastSeen(
                        object_class=cls_name,
                        class_id=last_det["class_id"],
                        last_bbox_x=last_det["bbox_x"],
                        last_bbox_y=last_det["bbox_y"],
                        last_bbox_w=last_det["bbox_w"],
                        last_bbox_h=last_det["bbox_h"],
                        last_snapshot_path=snapshot_path,
                        last_seen_at=now,
                        total_count=count,
                        camera_id=config.CAMERA_ID,
                    ))

                # 更新统计表
                stat = db.query(DetectionStat).filter_by(
                    stat_date=now.date(),
                    stat_hour=now.hour,
                    object_class=cls_name
                ).first()

                if stat:
                    stat.detection_count += count
                else:
                    db.add(DetectionStat(
                        stat_date=now.date(),
                        stat_hour=now.hour,
                        object_class=cls_name,
                        detection_count=count
                    ))

            db.commit()
        except Exception as e:
            db.rollback()
            print(f"❌ 推流数据库写入失败: {e}")
        finally:
            db.close()



    def get_current_frame_bytes(self) -> Optional[bytes]:
        """获取当前帧的 JPEG 字节流（用于 MJPEG 推流）"""
        with self._frame_lock:
            if self.current_frame is None:
                return None
            _, buffer = cv2.imencode(".jpg", self.current_frame,
                                     [cv2.IMWRITE_JPEG_QUALITY, 80])
            return buffer.tobytes()

    def get_status(self) -> Dict:
        """获取引擎当前状态"""
        return {
            "is_running": self.is_running,
            "fps": round(self.current_fps, 1),
            "frame_count": self.frame_count,
            "current_objects": len(self.current_detections),
            "model_loaded": self.model is not None,
            "source_type": self._source_type,
            "source": str(self._source) if self._source is not None else None,
        }


# 全局引擎实例
engine_instance = DetectionEngine()


