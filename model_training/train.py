import os
from ultralytics import YOLO

def main():
    """
    YOLOv11 训练启动脚本（适用于本地或云端算力服务器）
    """
    # 1. 加载预训练模型 (推荐先从 yolo11n.pt 纳米级模型开始，速度最快，显存占用最小)
    model = YOLO("yolo11n.pt") 

    # 2. 获取当前脚本所在目录，构建 yaml 的绝对或相对路径
    # 考虑到可能在其他路径运行此脚本，建议保持相对固定或使用绝对路径
    yaml_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data_pipeline', 'smarthome.yaml'))
    
    print(f"开始训练，使用配置文件: {yaml_path}")

    # 3. 启动训练
    # 参数说明：
    # epochs: 训练轮数
    # imgsz: 验证和训练时使用的图像分辨率（默认640）
    # batch: 批次大小，若显存不足请降低（如 16 或 8）
    # device: 0代表使用第一块显卡，若填 'cpu' 则使用 CPU 训练
    # workers: DataLoader 加载数据的线程数
    # save_period: 每隔10轮保存一次权重，防止因意外中断导致前功尽弃
    results = model.train(
        data=yaml_path,
        epochs=100, 
        imgsz=640,
        batch=32,       # 免费T4(16G显存)跑 nano 模型可以开大 batch，如32~64
        device=0, 
        workers=4,      # Colab 免费 CPU 偏弱，建议设为2或4，避免 CPU 瓶颈
        project="runs/train",
        name="smarthome_yolo11n",
        save_period=10, 
        amp=True        # 启用自动混合精度训练，节省显存并加速
    )

    print("✅ 训练完成！结果已保存在 runs/train/smarthome_yolo11n")

if __name__ == '__main__':
    main()
