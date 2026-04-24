"""
YOLO-SmartHome 快照生命周期清理器
定时清理过期的检测快照文件，防止磁盘空间无限增长
"""
import time
import threading
from pathlib import Path

from config import SNAPSHOTS_DIR, SNAPSHOT_RETAIN_DAYS


def cleanup_old_snapshots():
    """清理超过保留天数的快照文件"""
    cutoff = time.time() - SNAPSHOT_RETAIN_DAYS * 86400
    count = 0
    for f in Path(SNAPSHOTS_DIR).glob("*.jpg"):
        try:
            if f.stat().st_mtime < cutoff:
                f.unlink()
                count += 1
        except OSError:
            pass
    if count:
        print(f"🧹 已清理 {count} 张过期快照（>{SNAPSHOT_RETAIN_DAYS}天）")


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
