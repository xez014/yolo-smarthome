# 🏠 YOLO-SmartHome: 智能家居视觉感知与检索系统

![Vue.js](https://img.shields.io/badge/Frontend-Vue%203-4FC08D?logo=vue.js)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi)
![YOLO](https://img.shields.io/badge/Algorithm-YOLOv11-00FFFF?logo=pytorch)
![MySQL](https://img.shields.io/badge/Database-MySQL-4479A1?logo=mysql)

## 📖 项目简介
本项目为一个端到端的智能家居视觉感知系统，旨在让家庭环境具备“视觉记忆”。通过轻量级 YOLO 目标检测模型与多目标跟踪算法，系统不仅能实时识别家庭摄像头画面中的家具与物品，还能将其空间位置和时间戳存入数据库，实现类似“我的钥匙/笔记本最后出现在哪里”的**历史物品检索**功能。

本项目基于 MS COCO 2017 数据集进行了领域定制化的二次开发，提取了 20 类室内核心目标，构建了专属于本项目的 `SmartHome-COCO` 数据集。

## ✨ 核心功能
- **👁️ 实时环境感知：** 基于 YOLO 模型，实现对 20 类常见家居物品（沙发、桌子、笔记本、水杯等）的高帧率实时检测。
- **🧠 物品时空记忆：** 结合 ByteTrack 多目标跟踪算法，过滤闪烁目标，将物品出现的“时间+类别+画面相对位置”持久化至 MySQL 数据库。
- **🔍 历史轨迹检索：** 全栈驱动的 Web 控制台，支持按物品类别搜索其最近出现的监控画面截帧与确切时间。
- **📊 数据化看板：** 实时动态显示当前画面帧率、检测到的物品数量、以及家庭物品出现频次的统计图表。

## 🛠️ 技术栈
- **算法引擎层：** Python 3.10+, PyTorch, Ultralytics (YOLO), OpenCV, ByteTrack
- **后端中台层：** FastAPI, Uvicorn, SQLAlchemy (ORM)
- **前端交互层：** Vue 3, Element Plus, ECharts, Axios
- **数据持久层：** MySQL 8.0+

## 📂 项目目录结构
```text
yolo-smarthome/
│
├── data_pipeline/           # 数据工程模块
│   ├── SmartHome_COCO/      # 生成的专属数据集 (由脚本自动创建)
│   ├── data_pipeline.py     # COCO 数据提取与清洗脚本
│   └── smarthome.yaml       # YOLO 数据集配置文件
│
├── model_training/          # 算法模型模块
│   ├── train.py             # 模型训练脚本
│   ├── val.py               # 模型评估脚本
│   └── weights/             # 存放训练好的 best.pt 权重
│
├── backend/                 # FastAPI 后端模块
│   ├── main.py              # 后端服务入口
│   ├── database.py          # MySQL 数据库连接配置
│   ├── models.py            # 数据表 ORM 模型定义
│   └── routers/             # API 路由 (视频推流、数据查询)
│
├── frontend/                # Vue 3 前端模块
│   ├── src/
│   │   ├── components/      # UI 组件 (视频播放器、数据看板)
│   │   ├── views/           # 核心页面 (监控大屏页、历史检索页)
│   │   └── api/             # 后端接口请求封装
│   └── package.json
│
├── docs/                    # 项目文档
│   ├── 开题报告.md
│   └── 任务书.md
│
├── requirements.txt         # Python 依赖清单
└── README.md                # 项目说明文档
```


🚀 开发运行指南
阶段一：环境准备与数据清洗 (Data Pipeline)
安装 Python 核心依赖：
```bash
pip install -r requirements.txt
```
下载 MS COCO 2017 的 train2017, val2017, annotations，并解压至同级或指定目录。

运行数据清洗脚本，自动提取 20 类家居物品并转换为 YOLO 格式：

```Bash
cd data_pipeline
python data_pipeline.py
```

阶段二：模型训练 (Model Training)
确保 smarthome.yaml 配置路径正确。

启动 YOLO 训练：

```Bash
cd model_training
python train.py
```
阶段三：后端启动 (Backend Setup)
配置 backend/database.py 中的 MySQL 连接字符串（需提前在本地创建名为 smarthome_db 的数据库）。

启动 FastAPI 异步服务器：

```Bash
cd backend
uvicorn main:app --reload --port 8000
```
访问 http://127.0.0.1:8000/docs 查看自动生成的 API 接口文档。

阶段四：前端启动 (Frontend Setup)
安装 Node.js (推荐 v18+)。

安装前端依赖并启动开发服务器：

```Bash
cd frontend
npm install
npm run dev
```

📅 开发路线图 (Roadmap to 2026)
[ ] Milestone 1: 完成开题报告，跑通数据提取脚本，生成 SmartHome-COCO。

[ ] Milestone 2: 完成 YOLO 模型的训练与调优，PC 端摄像头推理 FPS > 30。

[ ] Milestone 3: 设计 MySQL 数据表，跑通 FastAPI 的视频推流接口。

[ ] Milestone 4: 完成 Vue 3 前端大屏开发，实现前后端数据联动。

[ ] Milestone 5: 撰写毕业论文，录制系统演示 Demo，准备答辩。