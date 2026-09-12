from __future__ import annotations

import io

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap


def make_qr_pixmap(data: str, size: int) -> QPixmap | None:
    """Tạo mã QR từ chuỗi `data`, trả về None nếu không tạo được (thiếu thư viện, dữ liệu rỗng...)."""
    if not data:
        return None
    try:
        import qrcode

        image = qrcode.make(data)
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        pixmap = QPixmap()
        pixmap.loadFromData(buffer.getvalue())
        return pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    except Exception:
        return None
