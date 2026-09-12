from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class TimerOverlay(QWidget):
    """Cửa sổ nhỏ, luôn nổi trên cùng, đếm ngược thời gian cho phần đang diễn ra.
    Đặt ở góc màn hình sân khấu để báo cáo viên canh giờ mà không cần rời mắt khỏi màn hình."""

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setFixedSize(150, 64)
        self.remaining_seconds = 0

        self.label = QLabel("00:00")
        self.label.setAlignment(Qt.AlignCenter)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.addWidget(self.label)
        self._set_overtime(False)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)

    def _set_overtime(self, overtime: bool) -> None:
        color = "#dc2626" if overtime else "#082f49"
        self.setStyleSheet(f"background: {color}; border-radius: 10px;")
        self.label.setStyleSheet(
            "color: white; font-size: 26px; font-weight: 800; font-family: 'Consolas', monospace; background: transparent;"
        )

    def start(self, minutes: int, screen_geometry=None) -> None:
        self.remaining_seconds = max(0, minutes) * 60
        self._set_overtime(False)
        self._render()
        if screen_geometry is not None:
            x = screen_geometry.x() + screen_geometry.width() - self.width() - 30
            y = screen_geometry.y() + screen_geometry.height() - self.height() - 30
            self.move(x, y)
        self.show()
        self.raise_()
        self.timer.start(1000)

    def stop(self) -> None:
        self.timer.stop()
        self.hide()

    def _tick(self) -> None:
        self.remaining_seconds -= 1
        self._set_overtime(self.remaining_seconds < 0)
        self._render()

    def _render(self) -> None:
        seconds = self.remaining_seconds
        sign = "-" if seconds < 0 else ""
        seconds = abs(seconds)
        minutes, secs = divmod(seconds, 60)
        self.label.setText(f"{sign}{minutes:02d}:{secs:02d}")
