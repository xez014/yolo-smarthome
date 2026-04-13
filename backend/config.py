"""
YOLO-SmartHome 配置管理模块
集中管理所有配置项，包括数据库连接、模型路径、检测参数等
"""
import os
from pathlib import Path

# === 项目路径 ===
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
WEIGHTS_PATH = str(PROJECT_ROOT / "results-01" / "runs" / "train_smarthome_s" / "weights" / "best.pt")
SNAPSHOTS_DIR = BASE_DIR / "snapshots"
SNAPSHOTS_DIR.mkdir(exist_ok=True)

# === 数据库配置 ===
DB_USER = os.getenv("DB_USER", "smarthome")
DB_PASSWORD = os.getenv("DB_PASSWORD", "20041122")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "smarthome_db")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

# === YOLO 检测配置 ===
CONFIDENCE_THRESHOLD = 0.25         # 检测置信度阈值（降低以提高召回率）
IOU_THRESHOLD = 0.5                 # NMS IoU 阈值
INPUT_SIZE = 640                    # 推理输入尺寸
DEVICE = "0"                        # GPU 设备号，'cpu' 为 CPU 模式

# === 追踪配置 ===
TRACKER_TYPE = "bytetrack.yaml"     # Ultralytics 内置追踪器配置
TRACK_PERSIST_FRAMES = 3           # track_id 持续 N 帧后才持久化到数据库 (调低以适配高帧率视频)

# === 快照 & 持久化配置 ===
SNAPSHOT_INTERVAL = 5               # 快照保存最小间隔（秒）
DB_WRITE_INTERVAL = 3               # 数据库写入最小间隔（秒）

# === 摄像头配置 ===
CAMERA_SOURCE = 0                   # 默认摄像头索引，也可以是视频文件路径
CAMERA_ID = "cam_01"                # 摄像头标识

# === 20 类家居物品 ===
CLASS_NAMES = [
    "chair", "couch", "potted plant", "bed", "dining table",
    "toilet", "tv", "laptop", "mouse", "remote",
    "keyboard", "cell phone", "microwave", "oven", "toaster",
    "sink", "refrigerator", "book", "clock", "vase"
]

# 中文映射（用于前端展示）
CLASS_NAMES_ZH = {
    "chair": "椅子", "couch": "沙发", "potted plant": "盆栽",
    "bed": "床", "dining table": "餐桌", "toilet": "马桶",
    "tv": "电视", "laptop": "笔记本电脑", "mouse": "鼠标",
    "remote": "遥控器", "keyboard": "键盘", "cell phone": "手机",
    "microwave": "微波炉", "oven": "烤箱", "toaster": "烤面包机",
    "sink": "水槽", "refrigerator": "冰箱", "book": "书籍",
    "clock": "时钟", "vase": "花瓶"
}

# === 服务配置 ===
CORS_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"]
