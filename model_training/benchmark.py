"""
YOLO-SmartHome 模型性能对比脚本
对比 YOLO11n 与 YOLO11s 在同一验证集上的精度-速度平衡
"""
from ultralytics import YOLO
from pathlib import Path
import time

# === 配置 ===
PROJECT_ROOT = Path(__file__).parent.parent
DATA_CONFIG = PROJECT_ROOT / "data_pipeline" / "smarthome_coco.yaml"

MODELS = {
    "YOLO11n": PROJECT_ROOT / "model_training" / "weights" / "best.pt",
    "YOLO11s": PROJECT_ROOT / "results-01" / "runs" / "train_smarthome_s" / "weights" / "best.pt",
}


def get_model_info(model):
    """获取模型参数量和文件大小"""
    n_params = sum(p.numel() for p in model.model.parameters())
    file_size_mb = Path(model.ckpt_path).stat().st_size / (1024 * 1024)
    return n_params, file_size_mb


def benchmark_inference(model, data_config, imgsz=640):
    """运行验证集评估并计时"""
    start = time.time()
    metrics = model.val(
        data=str(data_config),
        imgsz=imgsz,
        batch=16,
        verbose=False,
    )
    elapsed = time.time() - start
    return metrics, elapsed


def main():
    if not DATA_CONFIG.exists():
        print(f"❌ 数据集配置不存在: {DATA_CONFIG}")
        return

    results = []

    for name, weight_path in MODELS.items():
        if not weight_path.exists():
            print(f"⚠️ 跳过 {name}：权重文件 {weight_path} 不存在")
            continue

        print(f"\n{'=' * 60}")
        print(f"🔬 评估模型: {name}")
        print(f"   权重: {weight_path}")
        print(f"{'=' * 60}")

        model = YOLO(str(weight_path))
        n_params, file_size = get_model_info(model)
        metrics, elapsed = benchmark_inference(model, DATA_CONFIG)

        results.append({
            "name": name,
            "params": n_params,
            "size_mb": file_size,
            "map50": metrics.box.map50,
            "map": metrics.box.map,
            "precision": metrics.box.mp,
            "recall": metrics.box.mr,
            "eval_time": elapsed,
        })

    # === 输出 Markdown 对比表格 ===
    if not results:
        print("⚠️ 没有可用的模型进行对比")
        return

    print("\n\n" + "=" * 80)
    print("📊 YOLO11n vs YOLO11s 性能对比")
    print("=" * 80)

    # Markdown 表头
    print(f"\n| {'指标':<20s} |", end="")
    for r in results:
        print(f" {r['name']:>12s} |", end="")
    print()

    print(f"| {'-'*20} |", end="")
    for _ in results:
        print(f" {'-'*12} |", end="")
    print()

    # 表格行
    rows = [
        ("参数量", lambda r: f"{r['params']/1e6:.2f}M"),
        ("文件大小", lambda r: f"{r['size_mb']:.1f} MB"),
        ("Precision", lambda r: f"{r['precision']:.4f}"),
        ("Recall", lambda r: f"{r['recall']:.4f}"),
        ("mAP@0.5", lambda r: f"{r['map50']:.4f}"),
        ("mAP@0.5:0.95", lambda r: f"{r['map']:.4f}"),
        ("评估耗时", lambda r: f"{r['eval_time']:.1f}s"),
    ]

    for label, fmt in rows:
        print(f"| {label:<20s} |", end="")
        for r in results:
            print(f" {fmt(r):>12s} |", end="")
        print()

    print("\n✅ 对比完成！可将上方表格直接复制到论文中使用。")


if __name__ == "__main__":
    main()
