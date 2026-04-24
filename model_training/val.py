"""
YOLO-SmartHome 模型验证脚本
在验证集上评估当前最佳权重，生成混淆矩阵、PR 曲线等论文所需素材
"""
from ultralytics import YOLO
from pathlib import Path

# === 配置 ===
WEIGHTS = Path(__file__).parent.parent / "results-01" / "runs" / "train_smarthome_s" / "weights" / "best.pt"
DATA_CONFIG = Path(__file__).parent.parent / "data_pipeline" / "smarthome_coco.yaml"

def main():
    if not WEIGHTS.exists():
        print(f"❌ 权重文件不存在: {WEIGHTS}")
        return
    if not DATA_CONFIG.exists():
        print(f"❌ 数据集配置不存在: {DATA_CONFIG}")
        return

    print(f"📦 加载模型: {WEIGHTS}")
    model = YOLO(str(WEIGHTS))

    print(f"📊 开始验证集评估...")
    metrics = model.val(
        data=str(DATA_CONFIG),
        imgsz=640,
        batch=16,
        save_json=True,
        plots=True,       # 自动生成混淆矩阵、PR 曲线、F1 曲线
        verbose=True,
    )

    # === 输出总体指标 ===
    print("\n" + "=" * 60)
    print("📈 总体评估指标")
    print("=" * 60)
    print(f"  Precision:      {metrics.box.mp:.4f}")
    print(f"  Recall:         {metrics.box.mr:.4f}")
    print(f"  mAP@0.5:       {metrics.box.map50:.4f}")
    print(f"  mAP@0.5:0.95:  {metrics.box.map:.4f}")

    # === 输出每类指标 ===
    print("\n" + "-" * 60)
    print(f"{'类别':<20s} {'AP@0.5':>10s} {'AP@0.5:0.95':>12s}")
    print("-" * 60)
    names = metrics.names
    for i, name in names.items():
        ap50 = metrics.box.ap50[i]
        ap = metrics.box.ap[i]
        print(f"  {name:<18s} {ap50:>10.4f} {ap:>12.4f}")

    print("\n✅ 评估完成！可视化图表已保存至 runs/detect/val/ 目录")
    print("   - confusion_matrix.png    混淆矩阵")
    print("   - PR_curve.png            PR 曲线")
    print("   - F1_curve.png            F1 曲线")
    print("   - results.png             训练指标汇总图")


if __name__ == "__main__":
    main()
