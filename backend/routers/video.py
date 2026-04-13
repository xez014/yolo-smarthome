"""
YOLO-SmartHome 视频推流路由
提供 MJPEG 实时视频流和 WebSocket 实时检测数据推送
"""
import json
import asyncio
import time
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import StreamingResponse

from detection_engine import engine_instance
import config

router = APIRouter(prefix="/api/video", tags=["视频推流"])


@router.get("/stream")
async def video_stream():
    """
    MJPEG 实时视频流接口
    客户端通过 <img src="/api/video/stream"> 即可实时展示画面
    """
    def generate():
        while engine_instance.is_running:
            frame_bytes = engine_instance.get_current_frame_bytes()
            if frame_bytes:
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
                )
            time.sleep(0.033)  # ~30 FPS

    return StreamingResponse(
        generate(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket 实时检测数据推送
    推送当前帧的检测结果 JSON 数据（含 FPS、物品列表）
    """
    await websocket.accept()
    try:
        while True:
            if engine_instance.is_running:
                detections = engine_instance.current_detections
                data = {
                    "fps": round(engine_instance.current_fps, 1),
                    "frame_count": engine_instance.frame_count,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "current_objects": len(detections),
                    "detections": detections,
                }
                await websocket.send_text(json.dumps(data, ensure_ascii=False))
            else:
                await websocket.send_text(json.dumps({
                    "fps": 0, "frame_count": 0,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "current_objects": 0, "detections": [],
                }))
            await asyncio.sleep(0.5)  # 每 500ms 推送一次
    except WebSocketDisconnect:
        pass


@router.post("/start")
async def start_detection(source: str = Query(default=None, description="视频源（摄像头索引或视频文件路径）")):
    """
    启动摄像头推理
    - source: 不传则使用默认摄像头(0)，也可传入视频文件路径
    """
    src = None
    if source is not None:
        # 尝试转为整数（摄像头索引）
        try:
            src = int(source)
        except ValueError:
            src = source  # 视频文件路径

    result = engine_instance.start(source=src)
    return result


@router.post("/stop")
async def stop_detection():
    """停止推理"""
    result = engine_instance.stop()
    return result


@router.get("/status")
async def get_status():
    """获取推理引擎当前状态"""
    return engine_instance.get_status()
