# 🏠 YOLO-SmartHome: 智能家居视觉感知与检索系统

![Vue.js](https://img.shields.io/badge/Frontend-Vue%203-4FC08D?logo=vue.js)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi)
![YOLO](https://img.shields.io/badge/Algorithm-YOLOv11-00FFFF?logo=pytorch)
![Docker](https://img.shields.io/badge/Deployment-Docker-2496ED?logo=docker)
![MySQL](https://img.shields.io/badge/Database-MySQL-4479A1?logo=mysql)

## 📖 项目简介
本项目为一个端到端、工业级可部署的**智能家居视觉感知系统**，旨在让家庭环境具备“视觉记忆”。通过轻量级 YOLO 目标检测模型与多目标跟踪算法，系统不仅能实时识别家庭摄像头画面中的家具与物品，还能将其空间位置和时间戳存入数据库，实现类似“我的钥匙/笔记本最后出现在哪里”的**历史物品检索**功能。

本项目基于 MS COCO 2017 数据集进行了领域定制化的二次开发，提取了 20 类室内核心目标，构建了专属于本项目的 `SmartHome-COCO` 数据集。目前系统已完成所有的开发迭代，并支持一键 Docker 容器化上云部署。

## ✨ 核心功能
- **👁️ 实时环境感知：** 基于最新 YOLOv11 模型，实现对 20 类常见家居物品（沙发、桌子、笔记本、水杯等）的高帧率实时检测。
- **🧠 物品时空记忆：** 结合 ByteTrack 多目标跟踪算法与 Python 内存聚合去重机制，过滤闪烁目标，将物品出现的“时间+类别+画面相对位置”以及留存快照持久化至 MySQL 数据库。
- **🔍 历史轨迹检索：** 全栈驱动的 Web 控制台，支持按物品类别搜索其最近出现的监控画面截帧与确切时间。
- **📊 数据化看板：** 实时动态显示当前画面帧率、检测到的物品数量、以及家庭物品出现频次的统计图表。
- **🌐 全场景推流支持 (双模混动)：**
  - **云端拉流模式：** 支持直接拉取远程 RTSP 网络监控流、云服务器本地视频文件、服务器物理摄像头。
  - **客户端推流模式 (WebRTC Push)：** 支持在浏览器端直接调用本地笔记本摄像头或打开本地视频文件，通过 WebSocket 以二进制数据帧的方式实时推送到万里之外的云端 GPU 斩首服务器进行推理，并将实时画框结果无缝拉平回显。
- **🪄 傻瓜式安装向导：** 首次启动进入现代化图形界面，动态引导完成数据库建表及联通测试，全程 0 SQL 命令行接触。

## 🛠️ 技术栈
- **算法引擎层：** Python 3.11, PyTorch, Ultralytics (YOLOv11), OpenCV, ByteTrack
- **后端中台层：** FastAPI, Uvicorn, SQLAlchemy (ORM), WebSocket 双向推流
- **前端交互层：** Vue 3, Vite, Vue Router, Element Plus, ECharts, WebRTC (getUserMedia)
- **部署运维层：** Docker, Docker Compose, Nginx (反向代理与前后端同域化), 1Panel 网络对接
- **数据持久层：** MySQL 8.0+

## 📂 项目目录结构
```text
yolo-smarthome/
│
├── data_pipeline/           # 数据工程模块 (已跑通，产出 COCO 子集)
├── model_training/          # 算法模型模块 (已产出 best.pt 权重)
│
├── backend/                 # FastAPI 后端中台
│   ├── main.py              # 全局生命周期与服务入口
│   ├── detection_engine.py  # 核心引擎 (YOLO推理、ByteTrack追踪、内存聚合落库)
│   ├── config.py            # 动态 JSON 配置热加载
│   ├── database.py          # 懒加载 SQLAlchemy 连接池
│   ├── models.py            # ORM 实体类
│   ├── routers/             # API 路由
│   │   ├── setup.py         # 数据库初始化向导接口
│   │   ├── video.py         # WebSocket 双模推流与 MJPEG 接口
│   │   └── stats.py         # 聚合统计看板接口
│   └── data/                # [持久化挂载卷] - sqlite/json 等配置
│   └── snapshots/           # [持久化挂载卷] - 物品留存快照原图
│
├── frontend/                # Vue 3 前端应用
│   ├── src/
│   │   ├── components/      # (LocalStreamer 推流器、DetectionPanel 检测面板等)
│   │   ├── views/           # (Setup向导、Dashboard监控台、History历史检索)
│   │   ├── api/             # 同域相对路径 axios 封装
│   │   └── router/          # 全局路由拦截与守卫
│   ├── nginx.conf           # 生产级 Nginx 配置与 WebSocket 代理规则
│   └── Dockerfile.frontend  # Node.js 22 编译环境
│
├── docker-compose.yml       # 生产环境一键编排脚本 (已对接 1panel-network)
├── Dockerfile.backend       # 包含 OpenCV C++ 底层依赖的 Python 运行环境
└── README.md                # 项目说明文档
```


## 🚀 生产环境 一键部署指南 (Docker)

本系统已完全抛弃繁琐的本机环境配置，提供工业级的容器化傻瓜部署：

### 1. 代码拉取及编译
进入您的云服务器（支持 Debian/Ubuntu 等主流 Linux 或 IPv6-only 服务器），执行：
```bash
git clone https://github.com/xez014/yolo-smarthome.git
cd yolo-smarthome
docker compose up -d --build
```
*提示：初次构建因需要下载底层的 libgl1/libglib2 依赖以及 Node 22 环境，请耐心等待 3-5 分钟。*

### 2. 反向代理配置
服务启动后，前端监听在宿主机的 `10080` 端口。推荐使用 1Panel 或宝塔面板新建一个静态站点反向代理至 `http://127.0.0.1:10080`。
> **⚠️ 开启本地摄像头的必要条件**：现代浏览器安全策略强制规定，网页若要调用电脑内置摄像头（玩法三），必须在 **HTTPS** 协议下运行。请务必为您绑定的域名申请并在面板挂载 Let's Encrypt SSL 证书！

### 3. 图形化向导装配
配置完域名与 HTTPS 后，通过浏览器访问您的域名 `https://your-domain.com`，系统会自动拦截跳转至 **系统初始化向导 (Setup)**。
在页面填写您现有的 MySQL 数据库连通信息（如果使用 1Panel，Host 可以直接使用 `1panel-network` 内的容器内网 IP 或容器名称）。点击测试通过并初始化之后，系统自动为您在库中建表，完成装配并进入监控大屏。


## 💻 本地开发指南

如果您希望在本地 Windows/Mac 源码级运行并重构此项目：

1. **后端启动：**
   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn main:app --reload --port 8000
   ```
2. **前端启动：**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```


## 📅 项目状态 (Completed)

本项目作为毕业设计及展示级作品已达到 100% 开发完成度，以下里程碑均已兑现：
- [x] **Milestone 1:** 跑通数据提取脚本，提纯出 `SmartHome-COCO` 专供模型学习。
- [x] **Milestone 2:** 运用 Ultralytics 的 YOLO 工程体系将精度拔高，部署至服务器端推理。
- [x] **Milestone 3:** 跑通 FastAPI 异步处理管线与 RTSP 视频流，完美解决数据库重复高频写入的死锁。
- [x] **Milestone 4:** 开发出极具现代感和未来感的 Vue 3 监控大屏，并独创实现基于本地浏览器的 WebRTC 云端渲染推流架构。
- [x] **Milestone 5:** Nginx 代理跨域切割，容器化网络同传，全面达成 Docker 一键极速部署工业标准。