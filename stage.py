from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from core import Program
from qr_utils import make_qr_pixmap
from slide_export import resolve_report_photo, resolve_scene_image


class StageWindow(QWidget):
    escape_requested = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Màn hình trình chiếu")
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.simulate = False
        self.background_path = ""
        self.background = QPixmap()
        self.scene = {}
        self.program = Program()

        self.logo = QLabel()
        self.logo.setAlignment(Qt.AlignCenter)
        self.logo.setMaximumHeight(110)
        self.kicker = QLabel()
        self.kicker.setAlignment(Qt.AlignCenter)
        self.kicker.setObjectName("kicker")
        self.photo = QLabel()
        self.photo.setAlignment(Qt.AlignCenter)
        self.photo.setFixedSize(260, 300)
        self.photo.setObjectName("photo")
        self.title = QLabel()
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setWordWrap(True)
        self.title.setObjectName("title")
        self.subtitle = QLabel()
        self.subtitle.setAlignment(Qt.AlignCenter)
        self.subtitle.setWordWrap(True)
        self.subtitle.setObjectName("subtitle")
        self.qr = QLabel()
        self.qr.setAlignment(Qt.AlignCenter)

        content = QVBoxLayout(self)
        content.setContentsMargins(90, 55, 90, 65)
        content.addWidget(self.logo)
        content.addStretch(1)
        content.addWidget(self.kicker)
        speaker_row = QHBoxLayout()
        speaker_row.addStretch()
        speaker_row.addWidget(self.photo)
        speaker_row.addSpacing(55)
        text_box = QVBoxLayout()
        text_box.addWidget(self.title)
        text_box.addWidget(self.subtitle)
        speaker_row.addLayout(text_box, 1)
        speaker_row.addStretch()
        content.addLayout(speaker_row)
        content.addWidget(self.qr)
        content.addStretch(2)

        self.setStyleSheet("""
            QWidget { background: #082f49; color: white; font-family: "Segoe UI"; }
            QLabel { background: transparent; }
            QLabel#kicker { color: #bae6fd; font-size: 24px; font-weight: 600; }
            QLabel#title { color: white; font-size: 48px; font-weight: 800; }
            QLabel#subtitle { color: #dbeafe; font-size: 25px; }
            QLabel#photo { border: 3px solid rgba(255,255,255,0.8); border-radius: 14px; }
        """)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        if not self.background.isNull():
            scaled = self.background.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            x = (scaled.width() - self.width()) // 2
            y = (scaled.height() - self.height()) // 2
            painter.drawPixmap(0, 0, scaled, x, y, self.width(), self.height())
        else:
            painter.fillRect(self.rect(), Qt.GlobalColor.darkBlue)
        painter.fillRect(self.rect(), QColor(3, 37, 65, 185))

    def set_simulation_mode(self, enabled: bool) -> None:
        """Bật/tắt chế độ 'màn hình ảo': hiện dạng cửa sổ thường thay vì toàn màn hình,
        để test luồng chương trình khi không có màn hình chiếu/máy chiếu thật."""
        if self.simulate == enabled:
            return
        self.simulate = enabled
        was_visible = self.isVisible()
        self.hide()
        self.setWindowFlags(Qt.Window if enabled else Qt.FramelessWindowHint)
        if was_visible:
            self.show()

    def set_program(self, program: Program):
        self.program = program
        if program.logo and Path(program.logo).is_file():
            pix = QPixmap(program.logo).scaled(300, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.logo.setPixmap(pix)
        else:
            self.logo.clear()

    def _apply_background_for_scene(self, scene_type: str) -> None:
        path = resolve_scene_image(self.program, scene_type)
        self.background_path = path
        self.background = QPixmap(path) if path and Path(path).is_file() else QPixmap()

    def show_scene(self, scene: dict):
        self.scene = scene
        self._apply_background_for_scene(scene["type"])
        self.photo.hide()
        self.qr.hide()
        self.kicker.setText(self.program.event_name)
        scene_type = scene["type"]

        if scene_type == "speaker":
            report = scene["report"]
            self.kicker.setText(f"BÁO CÁO {scene['number']:02d}")
            self.title.setText(report.name.upper())
            details = [report.department, "", report.topic.upper()]
            self.subtitle.setText("\n".join(details))
            photo_path = resolve_report_photo(self.program, report)
            if photo_path and Path(photo_path).is_file():
                pix = QPixmap(photo_path).scaled(self.photo.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                self.photo.setPixmap(pix)
                self.photo.show()
        elif scene_type == "transition":
            self.title.setText(scene["title"])
            self.subtitle.setText(scene["report"].name)
        elif scene_type == "discussion":
            self.title.setText(scene["title"])
            self.subtitle.setText(f"Thời gian dự kiến: {scene['duration_minutes']} phút")
        elif scene_type == "post_test":
            self.title.setText(scene["title"])
            url = scene.get("url", "")
            pixmap = make_qr_pixmap(url, 280) if url else None
            if pixmap is not None:
                self.subtitle.setText("Quét mã QR để thực hiện bài kiểm tra")
                self.qr.setPixmap(pixmap)
                self.qr.show()
            elif url:
                self.subtitle.setText(url)
            else:
                self.subtitle.setText("Vui lòng cập nhật liên kết Post-test")
        else:
            self.title.setText(scene.get("title", ""))
            self.subtitle.setText(self.program.organizer)

        self.update()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.escape_requested.emit()
        super().keyPressEvent(event)
