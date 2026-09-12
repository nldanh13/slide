from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from paths import app_dir

BACKUPS_DIR = app_dir() / "backups"
MAX_BACKUPS_PER_FILE = 30


def create_backup(source_path: str) -> Path | None:
    """Sao chép file chương trình vừa lưu thành công thành một bản sao lưu có
    đánh dấu ngày giờ, để có thể khôi phục nếu chỉnh sửa nhầm. Không ném lỗi ra
    ngoài — sao lưu là tính năng phụ trợ, không được làm gián đoạn thao tác Lưu chính."""
    src = Path(source_path)
    if not src.is_file():
        return None
    try:
        BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = BACKUPS_DIR / f"{src.stem}__{timestamp}{src.suffix}"
        shutil.copy2(src, dest)
        _prune_old_backups(src.stem)
        return dest
    except OSError:
        return None


def _prune_old_backups(stem_prefix: str) -> None:
    backups = sorted(
        BACKUPS_DIR.glob(f"{stem_prefix}__*.json"),
        key=lambda p: p.stat().st_mtime,
    )
    excess = max(0, len(backups) - MAX_BACKUPS_PER_FILE)
    for path in backups[:excess]:
        path.unlink(missing_ok=True)


def list_backups() -> list[Path]:
    if not BACKUPS_DIR.is_dir():
        return []
    return sorted(BACKUPS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)


def backup_display_name(path: Path) -> str:
    """'chuong_trinh__20250101_153000.json' -> 'chuong_trinh — 01/01/2025 15:30:00'."""
    stem = path.stem
    if "__" in stem:
        name, _, stamp = stem.rpartition("__")
        try:
            when = datetime.strptime(stamp, "%Y%m%d_%H%M%S")
            return f"{name} — {when.strftime('%d/%m/%Y %H:%M:%S')}"
        except ValueError:
            pass
    return stem
