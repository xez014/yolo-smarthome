"""
YOLO-SmartHome 快照生命周期清理器
定时清理过期的检测快照文件，防止磁盘空间无限增长
"""
import time
import threading
from pathlib import Path

import database
from config import SNAPSHOTS_DIR, SNAPSHOT_RETAIN_DAYS
from models import DetectionRecord, ObjectLastSeen


def cleanup_old_snapshots():
    """清理超过保留天数的快照文件"""
    cutoff = time.time() - SNAPSHOT_RETAIN_DAYS * 86400
    count = 0
    removed_paths = []
    for f in Path(SNAPSHOTS_DIR).glob("*.jpg"):
        try:
            if f.stat().st_mtime < cutoff:
                f.unlink()
                count += 1
                removed_paths.append(f"/snapshots/{f.name}")
        except OSError:
            pass
    if removed_paths:
        clear_snapshot_refs(removed_paths)
    if count:
        print(f"🧹 已清理 {count} 张过期快照（>{SNAPSHOT_RETAIN_DAYS}天）")

def clear_snapshot_refs(snapshot_paths):
    """Remove database references to snapshot files that no longer exist."""
    if database.SessionLocal is None and not database.init_engine():
        return

    db = database.SessionLocal()
    try:
        db.query(DetectionRecord).filter(
            DetectionRecord.snapshot_path.in_(snapshot_paths)
        ).update({DetectionRecord.snapshot_path: None}, synchronize_session=False)
        db.query(ObjectLastSeen).filter(
            ObjectLastSeen.last_snapshot_path.in_(snapshot_paths)
        ).update({ObjectLastSeen.last_snapshot_path: None}, synchronize_session=False)
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


def start_cleaner(interval_hours=6):
    """启动后台定时清理线程（默认每6小时执行一次）"""
    def loop():
        while True:
            try:
                cleanup_old_snapshots()
            except Exception as e:
                print(f"⚠️ 快照清理出错: {e}")
            time.sleep(interval_hours * 3600)

    t = threading.Thread(target=loop, daemon=True, name="snapshot-cleaner")
    t.start()
    print(f"🧹 快照清理器已启动（保留 {SNAPSHOT_RETAIN_DAYS} 天，每 {interval_hours} 小时检查）")
