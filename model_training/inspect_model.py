"""
YOLO-SmartHome 模型分析脚本
查看 best.pt 的完整训练信息、各类别精度、并生成可视化图表
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from pathlib import Path
from ultralytics import YOLO
import torch
import csv

# === 路径配置 ===
WEIGHTS_PATH = Path(__file__).parent.parent / "results-01" / "runs" / "train_smarthome_s" / "weights" / "best.pt"
RESULTS_CSV = Path(__file__).parent.parent / "results-01" / "runs" / "train_smarthome_s" / "results.csv"
DATASET_YAML = Path(__file__).parent.parent / "data_pipeline" / "smarthome_coco.yaml"

CLASS_NAMES = [
    "chair", "couch", "potted plant", "bed", "dining table",
    "toilet", "tv", "laptop", "mouse", "remote",
    "keyboard", "cell phone", "microwave", "oven", "toaster",
    "sink", "refrigerator", "book", "clock", "vase"
]

CLASS_NAMES_ZH = {
    "chair": "椅子", "couch": "沙发", "potted plant": "盆栽",
    "bed": "床", "dining table": "餐桌", "toilet": "马桶",
    "tv": "电视", "laptop": "笔记本电脑", "mouse": "鼠标",
    "remote": "遥控器", "keyboard": "键盘", "cell phone": "手机",
    "microwave": "微波炉", "oven": "烤箱", "toaster": "烤面包机",
    "sink": "水槽", "refrigerator": "冰箱", "book": "书籍",
    "clock": "时钟", "vase": "花瓶"
}


def inspect_weights():
    """查看 best.pt 文件内容和元数据"""
    print("=" * 70)
    print("📋 模型权重文件信息")
    print("=" * 70)

    if not WEIGHTS_PATH.exists():
        print(f"❌ 权重文件不存在: {WEIGHTS_PATH}")
        return

    # 文件大小
    size_mb = WEIGHTS_PATH.stat().st_size / (1024 * 1024)
    print(f"📁 文件路径: {WEIGHTS_PATH}")
    print(f"📦 文件大小: {size_mb:.2f} MB")

    # 加载 checkpoint 查看原始元数据
    print("\n--- 原始 Checkpoint 元数据 ---")
    ckpt = torch.load(str(WEIGHTS_PATH), map_location="cpu", weights_only=False)

    if isinstance(ckpt, dict):
        print(f"🔑 Checkpoint 包含的键: {list(ckpt.keys())}")

        if "epoch" in ckpt:
            print(f"🔢 最佳 Epoch: {ckpt['epoch']}")
        if "best_fitness" in ckpt:
            print(f"🏆 Best Fitness: {ckpt['best_fitness']:.5f}")
        if "date" in ckpt:
            print(f"📅 训练日期: {ckpt['date']}")

        if "train_args" in ckpt:
            args = ckpt["train_args"]
            print(f"\n--- 训练参数 ---")
            important_keys = ["model", "data", "epochs", "batch", "imgsz", "device",
                              "optimizer", "lr0", "lrf", "momentum", "weight_decay",
                              "warmup_epochs", "amp", "workers"]
            for k in important_keys:
                if k in args:
                    print(f"  {k}: {args[k]}")

        if "train_metrics" in ckpt:
            print(f"\n--- 最佳 Epoch 指标 ---")
            for k, v in ckpt["train_metrics"].items():
                if isinstance(v, float):
                    print(f"  {k}: {v:.5f}")
                else:
                    print(f"  {k}: {v}")

        if "train_results" in ckpt:
            print(f"\n--- 训练结果摘要 ---")
            results = ckpt["train_results"]
            if isinstance(results, dict):
                for k, v in results.items():
                    print(f"  {k}: {v}")

    print()


def load_and_info():
    """通过 Ultralytics API 查看模型信息"""
    print("=" * 70)
    print("🧠 YOLO 模型结构信息")
    print("=" * 70)

    model = YOLO(str(WEIGHTS_PATH))

    # 模型信息
    print(f"📐 模型任务: {model.task}")
    print(f"📊 类别数量: {len(model.names)}")
    print(f"📋 类别映射:")
    for idx, name in model.names.items():
        zh = CLASS_NAMES_ZH.get(name, "")
        print(f"    {idx:>2}: {name:<15} ({zh})")

    # 模型参数量
    total_params = sum(p.numel() for p in model.model.parameters())
    trainable_params = sum(p.numel() for p in model.model.parameters() if p.requires_grad)
    print(f"\n🔢 总参数量: {total_params:,} ({total_params/1e6:.2f}M)")
    print(f"🔧 可训练参数: {trainable_params:,} ({trainable_params/1e6:.2f}M)")

    return model


def analyze_training_curve():
    """分析训练曲线（从 results.csv）"""
    print("\n" + "=" * 70)
    print("📈 训练曲线分析")
    print("=" * 70)

    if not RESULTS_CSV.exists():
        print(f"❌ results.csv 不存在: {RESULTS_CSV}")
        return

    rows = []
    with open(RESULTS_CSV, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # 清理列名（去除空格）
            cleaned = {k.strip(): v.strip() for k, v in row.items()}
            rows.append(cleaned)

    if not rows:
        print("⚠️ CSV 文件为空")
        return

    total_epochs = len(rows)
    last = rows[-1]
    best_map50 = max(float(r.get("metrics/mAP50(B)", 0)) for r in rows)
    best_map50_epoch = next(i + 1 for i, r in enumerate(rows)
                           if float(r.get("metrics/mAP50(B)", 0)) == best_map50)
    best_map5095 = max(float(r.get("metrics/mAP50-95(B)", 0)) for r in rows)

    print(f"📊 总训练轮次: {total_epochs} epochs")
    print(f"⏱️  总训练时间: {float(last.get('time', 0))/3600:.1f} 小时")
    print()

    # 最终指标
    print("--- 最终 Epoch (第 {}) 的指标 ---".format(total_epochs))
    print(f"  Precision:   {float(last.get('metrics/precision(B)', 0)):.4f}")
    print(f"  Recall:      {float(last.get('metrics/recall(B)', 0)):.4f}")
    print(f"  mAP@0.5:     {float(last.get('metrics/mAP50(B)', 0)):.4f}")
    print(f"  mAP@0.5:0.95:{float(last.get('metrics/mAP50-95(B)', 0)):.4f}")
    print()

    # 最佳指标
    print("--- 最佳指标 ---")
    print(f"  最佳 mAP@0.5:     {best_map50:.4f} (Epoch {best_map50_epoch})")
    print(f"  最佳 mAP@0.5:0.95: {best_map5095:.4f}")
    print()

    # 损失变化
    first = rows[0]
    print("--- 损失函数变化 (Epoch 1 → {}) ---".format(total_epochs))
    for loss_key in ["train/box_loss", "train/cls_loss", "train/dfl_loss"]:
        v_first = float(first.get(loss_key, 0))
        v_last = float(last.get(loss_key, 0))
        change = ((v_last - v_first) / v_first) * 100
        print(f"  {loss_key}: {v_first:.4f} → {v_last:.4f} ({change:+.1f}%)")

    for loss_key in ["val/box_loss", "val/cls_loss", "val/dfl_loss"]:
        v_first = float(first.get(loss_key, 0))
        v_last = float(last.get(loss_key, 0))
        change = ((v_last - v_first) / v_first) * 100
        print(f"  {loss_key}: {v_first:.4f} → {v_last:.4f} ({change:+.1f}%)")

    # 是否还在收敛
    print()
    print("--- 收敛性判断 ---")
    if total_epochs >= 5:
        last5_maps = [float(rows[-(i+1)].get("metrics/mAP50(B)", 0)) for i in range(5)]
        improvement = last5_maps[0] - last5_maps[-1]
        print(f"  最后5轮 mAP@0.5 变化: {last5_maps[-1]:.4f} → {last5_maps[0]:.4f} (Δ={improvement:+.4f})")
        if abs(improvement) < 0.005:
            print("  📉 模型已基本收敛，继续训练提升空间有限")
        elif improvement > 0:
            print("  📈 模型仍在收敛，可以考虑继续训练更多 Epoch")
        else:
            print("  ⚠️ 最后几轮指标下降，可能出现过拟合")

    # mAP 水平评估
    print()
    print("--- mAP 水平评估 ---")
    map50 = float(last.get("metrics/mAP50(B)", 0))
    if map50 >= 0.7:
        print(f"  ✅ mAP@0.5={map50:.1%}，表现良好")
    elif map50 >= 0.5:
        print(f"  ⚠️ mAP@0.5={map50:.1%}，中等水平")
        print("  💡 建议：")
        print("     1. 增加训练轮次（当前仅79轮，可到150-200轮）")
        print("     2. 尝试更大的模型（yolo11s.pt 或 yolo11m.pt 替代 yolo11n.pt）")
        print("     3. 使用更大的图片尺寸（imgsz=800 或 1024）")
        print("     4. 调整数据增强策略")
    else:
        print(f"  ❌ mAP@0.5={map50:.1%}，表现较差，需要优化")


def run_validation(model):
    """在验证集上运行完整评估，查看各类别精度"""
    print("\n" + "=" * 70)
    print("🔍 各类别详细精度评估（验证集）")
    print("=" * 70)

    if not DATASET_YAML.exists():
        print(f"⚠️ 数据集配置不存在: {DATASET_YAML}")
        print("跳过逐类评估。如需评估，请确保 SmartHome_COCO 数据集存在")
        return

    try:
        results = model.val(data=str(DATASET_YAML), imgsz=640, verbose=False)

        print(f"\n{'类别':<18} {'Precision':>10} {'Recall':>10} {'mAP@0.5':>10} {'mAP@0.5:0.95':>13}")
        print("-" * 65)

        # 总体指标
        mp = results.results_dict.get("metrics/precision(B)", 0)
        mr = results.results_dict.get("metrics/recall(B)", 0)
        map50 = results.results_dict.get("metrics/mAP50(B)", 0)
        map5095 = results.results_dict.get("metrics/mAP50-95(B)", 0)
        print(f"{'总计 (ALL)':<18} {mp:>10.4f} {mr:>10.4f} {map50:>10.4f} {map5095:>13.4f}")
        print("-" * 65)

        # 各类别指标
        if hasattr(results, 'box') and results.box is not None:
            ap50 = results.box.ap50
            ap = results.box.ap
            p = results.box.p
            r = results.box.r

            # 按 mAP@0.5 排序
            class_data = []
            for i, name in enumerate(CLASS_NAMES):
                if i < len(ap50):
                    zh = CLASS_NAMES_ZH.get(name, "")
                    label = f"{zh}({name})"
                    class_data.append((label, float(p[i]), float(r[i]), float(ap50[i]), float(ap[i])))

            class_data.sort(key=lambda x: x[3], reverse=True)
            for label, pi, ri, ap50i, api in class_data:
                flag = "✅" if ap50i >= 0.6 else ("⚠️" if ap50i >= 0.4 else "❌")
                print(f"{flag} {label:<16} {pi:>10.4f} {ri:>10.4f} {ap50i:>10.4f} {api:>13.4f}")

            # 识别弱类
            print("\n--- 弱类识别（mAP@0.5 < 0.5 的类别）---")
            weak = [(l, a) for l, _, _, a, _ in class_data if a < 0.5]
            if weak:
                for label, a in weak:
                    print(f"  ❌ {label}: mAP@0.5={a:.4f}")
                print(f"\n  💡 弱类优化建议：")
                print(f"     1. 检查这些类别在训练集中的样本数量是否充足")
                print(f"     2. 这些物品可能因为太小或容易混淆导致检测困难")
                print(f"     3. 可以针对弱类增加带有这些物品的训练图片")
            else:
                print("  ✅ 没有明显的弱类")

    except Exception as e:
        print(f"⚠️ 验证评估失败: {e}")
        print("  可能原因：SmartHome_COCO 数据集不在本地")


def main():
    print("\n" + "🏠 YOLO-SmartHome 模型完整分析报告".center(70))
    print("=" * 70)

    # 1. 查看权重文件元数据
    inspect_weights()

    # 2. YOLO API 查看模型信息
    model = load_and_info()

    # 3. 分析训练曲线
    analyze_training_curve()

    # 4. 逐类精度验证（如果有数据集）
    run_validation(model)

    print("\n" + "=" * 70)
    print("✅ 分析报告生成完毕")
    print("=" * 70)


if __name__ == "__main__":
    main()
