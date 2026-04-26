# YOLO11n vs YOLO11s 性能对比表

评估命令：`.venv\Scripts\python.exe model_training\benchmark.py`

评估数据：SmartHome-COCO 验证集，1899 张图片，6962 个实例。

评估环境：CPU，12th Gen Intel Core i7-12700H；Ultralytics 8.4.37；Python 3.11.9；torch 2.11.0+cpu。

| 指标 | YOLO11n | YOLO11s |
| --- | ---: | ---: |
| 参数量 | 2.59M | 9.44M |
| 文件大小 | 15.2 MB | 54.4 MB |
| Precision | 0.6964 | 0.6775 |
| Recall | 0.5230 | 0.6144 |
| mAP@0.5 | 0.6013 | 0.6552 |
| mAP@0.5:0.95 | 0.4384 | 0.4849 |
| 评估耗时 | 109.7s | 275.7s |
