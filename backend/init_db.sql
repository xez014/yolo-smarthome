-- ============================================
-- YOLO-SmartHome 数据库初始化脚本
-- 用于手动建表参考，系统会通过 SQLAlchemy ORM 自动建表
-- ============================================

-- 创建数据库（如果尚未创建）
-- CREATE DATABASE IF NOT EXISTS smarthome_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
-- USE smarthome_db;

-- 1. 物品检测记录表
CREATE TABLE IF NOT EXISTS detection_records (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    object_class VARCHAR(50) NOT NULL COMMENT '物品类别名称',
    class_id INT NOT NULL COMMENT '类别ID (0-19)',
    confidence FLOAT NOT NULL COMMENT '检测置信度',
    bbox_x FLOAT NOT NULL COMMENT '边界框中心X (归一化)',
    bbox_y FLOAT NOT NULL COMMENT '边界框中心Y (归一化)',
    bbox_w FLOAT NOT NULL COMMENT '边界框宽度 (归一化)',
    bbox_h FLOAT NOT NULL COMMENT '边界框高度 (归一化)',
    track_id INT COMMENT 'ByteTrack 追踪ID',
    snapshot_path VARCHAR(255) COMMENT '截帧快照路径',
    detected_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '检测时间',
    camera_id VARCHAR(50) DEFAULT 'cam_01' COMMENT '摄像头标识',
    INDEX idx_class (object_class),
    INDEX idx_detected_at (detected_at),
    INDEX idx_class_time (object_class, detected_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. 物品最后出现位置表
CREATE TABLE IF NOT EXISTS object_last_seen (
    id INT AUTO_INCREMENT PRIMARY KEY,
    object_class VARCHAR(50) NOT NULL UNIQUE COMMENT '物品类别',
    class_id INT NOT NULL,
    last_bbox_x FLOAT,
    last_bbox_y FLOAT,
    last_bbox_w FLOAT,
    last_bbox_h FLOAT,
    last_snapshot_path VARCHAR(255) COMMENT '最后一次出现的快照',
    last_seen_at DATETIME NOT NULL COMMENT '最后出现时间',
    total_count INT DEFAULT 0 COMMENT '累计出现次数',
    camera_id VARCHAR(50) DEFAULT 'cam_01',
    INDEX idx_last_seen_at (last_seen_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. 统计概要表
CREATE TABLE IF NOT EXISTS detection_stats (
    id INT AUTO_INCREMENT PRIMARY KEY,
    stat_date DATE NOT NULL COMMENT '统计日期',
    stat_hour INT COMMENT '统计小时 (0-23), NULL表示全天',
    object_class VARCHAR(50) NOT NULL,
    detection_count INT DEFAULT 0 COMMENT '检测次数',
    UNIQUE KEY uk_stat (stat_date, stat_hour, object_class)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
