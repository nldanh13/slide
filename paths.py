from __future__ import annotations

import sys
from pathlib import Path


def app_dir() -> Path:
    """Thư mục chứa ứng dụng: cạnh file .exe khi đóng gói bằng PyInstaller,
    hoặc cạnh mã nguồn khi chạy trực tiếp bằng python."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent
