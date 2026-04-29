import os
from ultralytics import YOLO

def main():
    """
    YOLOv11 训练启动脚本（适用于本地或云端算力服务器）
    """
    # 1. 加载 YOLO11s 预训练模型，作为本文生产推理权重的训练起点
    model = YOLO("yolo11s.pt")

    # 2. 获取当前脚本所在目录，构建 yaml 的绝对或相对路径
    # 考虑到可能在其他路径运行此脚本，建议保持相对固定或使用绝对路径
    yaml_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data_pipeline', 'smarthome.yaml'))
    project_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'results-01', 'runs'))
    
    print(f"开始训练，使用配置文件: {yaml_path}")

    # 3. 启动训练
    # 参数说明：
    # epochs: 训练轮数
    # imgsz: 验证和训练时使用的图像分辨率（默认640）
    # batch: 批次大小，若显存不足请降低（如 16 或 8）
    # device: "0,1" 表示使用两块 GPU，单卡或 CPU 环境可改为 0 或 'cpu'
    # workers: DataLoader 加载数据的线程数
    # save_period: 每隔10轮保存一次权重，防止因意外中断导致前功尽弃
    results = model.train(
        data=yaml_path,
        epochs=100,
        imgsz=640,
        batch=16,
        device="0,1",
        workers=4,
        project=project_path,
        name="train_smarthome_s",
        save_period=10,
        amp=True        # 启用自动混合精度训练，节省显存并加速
    )

    print(f"✅ 训练完成！结果已保存在 {os.path.join(project_path, 'train_smarthome_s')}")

if __name__ == '__main__':
    main()
