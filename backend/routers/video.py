"""
YOLO-SmartHome 视频推流路由
提供 MJPEG 实时视频流和 WebSocket 实时检测数据推送
"""
import json
import asyncio
import time
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
from fastapi.responses import StreamingResponse

from detection_engine import engine_instance
from auth import get_current_user, verify_ws_token
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
            status = engine_instance.get_status()
            if status["is_running"]:
                detections = engine_instance.current_detections
                data = {
                    "fps": status["fps"],
                    "frame_count": status["frame_count"],
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "current_objects": status["current_objects"],
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


@router.websocket("/ws/push")
async def push_inference_endpoint(
    websocket: WebSocket,
    token: str = Query(default=""),
    source_type: str = Query(default="push"),
):
    """
    客户端推流推理 WebSocket
    浏览器发送原始 JPEG 帧字节 → 服务端 YOLO 推理 → 返回 JSON {image: base64, detections: [...]}
    需通过 ?token=xxx 传递认证令牌
    """
    # WebSocket 鉴权
    if not verify_ws_token(token):
        await websocket.close(code=4001, reason="认证失败")
        return

    await websocket.accept()
    engine_instance.register_push_client(source_type)
    import base64
    try:
        while True:
            # 接收来自浏览器的原始 JPEG 二进制帧
            raw_bytes = await websocket.receive_bytes()

            # 在推理引擎上执行无状态单帧推理
            annotated_bytes, detections = engine_instance.infer_single_frame(raw_bytes)

            if annotated_bytes is None:
                await websocket.send_text(json.dumps({"error": "模型未加载"}))
                continue

            # 返回 base64 编码的标注帧 + 检测列表
            b64_image = base64.b64encode(annotated_bytes).decode("utf-8")
            await websocket.send_text(json.dumps({
                "image": f"data:image/jpeg;base64,{b64_image}",
                "detections": detections,
                "current_objects": len(detections),
            }, ensure_ascii=False))

    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"Push WS error: {e}")
    finally:
        engine_instance.unregister_push_client()



@router.post("/start")
async def start_detection(
    source: str = Query(default=None, description="视频源（摄像头索引或视频文件路径）"),
    user: str = Depends(get_current_user)
):
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
async def stop_detection(user: str = Depends(get_current_user)):
    """停止推理"""
    result = engine_instance.stop()
    return result


@router.get("/status")
async def get_status(user: str = Depends(get_current_user)):
    """获取推理引擎当前状态"""
    return engine_instance.get_status()
