# YOLO11s 每类 AP 评估表

评估命令：`.venv\Scripts\python.exe model_training\val.py`

评估数据：SmartHome-COCO 验证集，1899 张图片，6962 个实例。

总体指标：Precision 0.6775，Recall 0.6144，mAP@0.5 0.6552，mAP@0.5:0.95 0.4849。

| 类别 | AP@0.5 | AP@0.5:0.95 |
| --- | ---: | ---: |
| chair | 0.5471 | 0.3584 |
| couch | 0.6917 | 0.5365 |
| potted plant | 0.5130 | 0.3142 |
| bed | 0.6897 | 0.5269 |
| dining table | 0.5541 | 0.4130 |
| toilet | 0.8459 | 0.6796 |
| tv | 0.8161 | 0.6336 |
| laptop | 0.8163 | 0.6838 |
| mouse | 0.7661 | 0.5930 |
| remote | 0.5364 | 0.3406 |
| keyboard | 0.7350 | 0.5585 |
| cell phone | 0.5615 | 0.3952 |
| microwave | 0.8180 | 0.6692 |
| oven | 0.6537 | 0.4655 |
| toaster | 0.5580 | 0.3906 |
| sink | 0.6419 | 0.4285 |
| refrigerator | 0.7859 | 0.6466 |
| book | 0.2541 | 0.1373 |
| clock | 0.7516 | 0.5307 |
| vase | 0.5679 | 0.3967 |
