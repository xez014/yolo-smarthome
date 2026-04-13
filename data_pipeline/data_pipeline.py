import os
import shutil
import sys
import subprocess
from pathlib import Path

# 环境自检与自动安装依赖
def install_requirements():
    try:
        from pycocotools.coco import COCO
        import tqdm
    except ImportError:
        print("Required packages pycocotools or tqdm not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pycocotools", "tqdm"])

install_requirements()

from pycocotools.coco import COCO
from tqdm import tqdm

# 目标提取类别：20类家居或电器
TARGET_CLASSES = [
    'chair', 'couch', 'potted plant', 'bed', 'dining table', 
    'toilet', 'tv', 'laptop', 'mouse', 'remote', 
    'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 
    'sink', 'refrigerator', 'book', 'clock', 'vase'
]

# 配置路径
ROOT_DIR = Path(__file__).resolve().parent.parent
COCO_DIR = ROOT_DIR / 'coco2017'

# 处理不同的 COCO 目录结构 (如果是独立 annotations 文件夹或嵌套在 annotations_trainval2017 中)
ANN_DIR = COCO_DIR / 'annotations'
if not ANN_DIR.exists():
    ANN_DIR = COCO_DIR / 'annotations_trainval2017' / 'annotations'

OUTPUT_DIR = ROOT_DIR / 'data_pipeline' / 'SmartHome_COCO'

def check_coco_exists():
    """检查 COCO 原始数据集是否已放置在正确位置"""
    if not COCO_DIR.exists():
        print(f"Error: COCO directory not found at {COCO_DIR}.")
        print("请将解压后的 COCO 数据放置在该位置 (yolo-smarthome/coco2017/)")
        print("预期格式应包含: annotations/, train2017/, val2017/")
        sys.exit(1)
        
    if not ANN_DIR.exists() or not (COCO_DIR / 'train2017').exists() or not (COCO_DIR / 'val2017').exists():
         print("Could not find the expected COCO folders (annotations, train2017, val2017). Please check the layout.")
         sys.exit(1)

def convert_bbox_coco2yolo(img_width, img_height, bbox):
    """
    将 COCO [x_min, y_min, width, height] 转换为 YOLO 归一化格式 [x_center, y_center, width, height]
    """
    x_min, y_min, w, h = bbox
    center_x = (x_min + w / 2) / img_width
    center_y = (y_min + h / 2) / img_height
    norm_w = w / img_width
    norm_h = h / img_height
    return [center_x, center_y, norm_w, norm_h]

def process_dataset(data_type):
    """处理 train 或 val 数据集"""
    print(f"--- Processing {data_type}2017 ---")
    ann_file = ANN_DIR / f'instances_{data_type}2017.json'
    coco = COCO(str(ann_file))
    
    # 获取目标类别的 catId 列表
    cat_ids = coco.getCatIds(catNms=TARGET_CLASSES)
    if not cat_ids:
        print("未找到任何目标类别！请检查 TARGET_CLASSES 列表与 COCO 是否匹配。")
        return 0
    
    # 建立 COCO catId 到 自定义 0-19 索引的映射
    coco_cats = coco.loadCats(cat_ids)
    category_name_to_id = {cat['name']: cat['id'] for cat in coco_cats}
    cat_id_to_yolo_id = {}
    for yolo_id, cls_name in enumerate(TARGET_CLASSES):
        if cls_name in category_name_to_id:
            cat_id_to_yolo_id[category_name_to_id[cls_name]] = yolo_id

    # 查询包含任意一个目标类别的图像 ID
    img_ids = []
    for catId in cat_ids:
        img_ids.extend(coco.getImgIds(catIds=[catId]))
    # 去重
    img_ids = list(set(img_ids))
    print(f"Found {len(img_ids)} images containing target classes in {data_type}2017.")
    
    # 全自动目录创建
    out_images_dir = OUTPUT_DIR / 'images' / ('train' if data_type == 'train' else 'val')
    out_labels_dir = OUTPUT_DIR / 'labels' / ('train' if data_type == 'train' else 'val')
    out_images_dir.mkdir(parents=True, exist_ok=True)
    out_labels_dir.mkdir(parents=True, exist_ok=True)
    
    src_images_dir = COCO_DIR / f"{data_type}2017"
    
    processed_count = 0
    for img_id in tqdm(img_ids, desc=f"Converting {data_type}2017"):
        img_info = coco.loadImgs(img_id)[0]
        file_name = img_info['file_name']
        img_w = img_info['width']
        img_h = img_info['height']
        
        src_img_path = src_images_dir / file_name
        dst_img_path = out_images_dir / file_name
        
        # 获取该图像的指定类别的标注
        ann_ids = coco.getAnnIds(imgIds=img_id, catIds=cat_ids, iscrowd=False)
        anns = coco.loadAnns(ann_ids)
        
        if not anns:
            continue
            
        label_file_path = out_labels_dir / file_name.replace('.jpg', '.txt')
        
        # 写入 YOLO 格式的标签
        with open(label_file_path, 'w') as f:
            for ann in anns:
                if ann['category_id'] not in cat_id_to_yolo_id:
                    continue
                yolo_cls_id = cat_id_to_yolo_id[ann['category_id']]
                yolo_bbox = convert_bbox_coco2yolo(img_w, img_h, ann['bbox'])
                # format: class_index center_x center_y width height
                line = f"{yolo_cls_id} {yolo_bbox[0]:.6f} {yolo_bbox[1]:.6f} {yolo_bbox[2]:.6f} {yolo_bbox[3]:.6f}\n"
                f.write(line)
        
        # 复制图片
        if not dst_img_path.exists() and src_img_path.exists():
            shutil.copy(src_img_path, dst_img_path)
            
        processed_count += 1
        
    return processed_count

def main():
    print("检查环境与数据存放路径...")
    check_coco_exists()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print("Starting data pipeline...")
    train_count = process_dataset('train')
    val_count = process_dataset('val')
    
    print("\n=======================================")
    print("数据提取与转换完成!")
    print(f"成功提取的训练集 (train) 图片数量: {train_count}")
    print(f"成功提取的验证集 (val) 图片数量: {val_count}")
    print(f"转化后的 YOLO 格式数据集已存储至: {OUTPUT_DIR}")
    print("=======================================")

if __name__ == '__main__':
    main()
