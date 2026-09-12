from __future__ import annotations

import io
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QAction, QFont, QKeySequence, QPainter, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core import Program, Report, validate_program
from powerpoint import PowerPointController, PowerPointError
from remote import RemoteControl


APP_STYLE = """
QWidget { font-family: "Segoe UI"; font-size: 10pt; color: #162033; }
QMainWindow, QDialog { background: #f4f7fb; }
QLineEdit, QSpinBox, QComboBox, QTableWidget {
    background: white; border: 1px solid #ccd5e2; border-radius: 6px; padding: 6px;
}
QTableWidget { gridline-color: #e5eaf1; }
QHeaderView::section { background: #e8eef7; padding: 8px; border: 0; font-weight: 600; }
QPushButton { background: #e6edf7; border: 0; border-radius: 7px; padding: 8px 14px; }
QPushButton:hover { background: #d8e3f3; }
QPushButton#primary { background: #075985; color: white; font-weight: 700; }
QPushButton#primary:hover { background: #0369a1; }
QPushButton#danger { background: #fee2e2; color: #991b1b; }
"""


def choose_file(parent, title, file_filter):
    value, _ = QFileDialog.getOpenFileName(parent, title, "", file_filter)
    return value


class ReportDialog(QDialog):
    def __init__(self, parent=None, report: Report | None = None):
        super().__init__(parent)
        self.setWindowTitle("Thông tin báo cáo viên")
        self.setMinimumWidth(650)
        report = report or Report()

        self.name = QLineEdit(report.name)
        self.department = QLineEdit(report.department)
        self.topic = QLineEdit(report.topic)
        self.photo = QLineEdit(report.photo)
        self.ppt = QLineEdit(report.ppt)
        self.duration = QSpinBox()
        self.duration.setRange(1, 240)
        self.duration.setValue(report.duration_minutes)

        form = QFormLayout()
        form.addRow("Họ tên, học hàm/học vị*", self.name)
        form.addRow("Đơn vị", self.department)
        form.addRow("Tên chuyên đề*", self.topic)
        form.addRow("Ảnh báo cáo viên", self._path_row(self.photo, "Ảnh (*.png *.jpg *.jpeg)"))
        form.addRow("File PowerPoint*", self._path_row(self.ppt, "PowerPoint (*.ppt *.pptx *.pptm *.pps *.ppsx)"))
        form.addRow("Thời lượng dự kiến (phút)", self.duration)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText("Lưu")
        buttons.button(QDialogButtonBox.Cancel).setText("Hủy")
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def _path_row(self, edit, file_filter):
        box = QWidget()
        row = QHBoxLayout(box)
        row.setContentsMargins(0, 0, 0, 0)
        button = QPushButton("Chọn…")
        button.clicked.connect(
            lambda: (value := choose_file(self, "Chọn file", file_filter)) and edit.setText(value)
        )
        row.addWidget(edit, 1)
        row.addWidget(button)
        return box

    def _accept(self):
        if not self.name.text().strip() or not self.topic.text().strip() or not self.ppt.text().strip():
            QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng nhập họ tên, chuyên đề và chọn file PowerPoint.")
            return
        self.accept()

    def report(self):
        return Report(
            name=self.name.text().strip(),
            department=self.department.text().strip(),
            topic=self.topic.text().strip(),
            photo=self.photo.text().strip(),
            ppt=self.ppt.text().strip(),
            duration_minutes=self.duration.value(),
        )


class RemoteDialog(QDialog):
    def __init__(self, parent, remote: RemoteControl):
        super().__init__(parent)
        self.setWindowTitle("Điều khiển từ xa")
        self.setMinimumWidth(360)

        url = remote.url()

        info = QLabel(
            "Dùng điện thoại kết nối cùng Wi-Fi với máy tính này, quét mã QR "
            "hoặc mở đường dẫn bên dưới bằng trình duyệt để điều khiển chương trình."
        )
        info.setWordWrap(True)

        qr_label = QLabel()
        qr_label.setAlignment(Qt.AlignCenter)
        try:
            import qrcode

            image = qrcode.make(url)
            data = io.BytesIO()
            image.save(data, format="PNG")
            pix = QPixmap()
            pix.loadFromData(data.getvalue())
            qr_label.setPixmap(pix.scaled(240, 240, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        except Exception:
            qr_label.setText("Không tạo được mã QR")

        link = QLineEdit(url)
        link.setReadOnly(True)

        note = QLabel(
            "Lưu ý: liên kết chỉ dùng được khi điện thoại và máy tính cùng mạng Wi-Fi. "
            "Khởi động lại ứng dụng sẽ tạo mã truy cập mới."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color: #64748b; font-size: 9pt;")

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.button(QDialogButtonBox.Close).setText("Đóng")
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)

        layout = QVBoxLayout(self)
        layout.addWidget(info)
        layout.addWidget(qr_label)
        layout.addWidget(link)
        layout.addWidget(note)
        layout.addWidget(buttons)


class StageWindow(QWidget):
    escape_requested = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Màn hình trình chiếu")
        self.setWindowFlags(Qt.FramelessWindowHint)
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
        painter.fillRect(self.rect(), QColorWithAlpha(3, 37, 65, 185))

    def set_program(self, program: Program):
        self.program = program
        self.background_path = program.background
        self.background = QPixmap(program.background) if program.background else QPixmap()
        if program.logo and Path(program.logo).is_file():
            pix = QPixmap(program.logo).scaled(300, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.logo.setPixmap(pix)
        else:
            self.logo.clear()
        self.update()

    def show_scene(self, scene: dict):
        self.scene = scene
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
            if report.photo and Path(report.photo).is_file():
                pix = QPixmap(report.photo).scaled(self.photo.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
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
            self.subtitle.setText("Quét mã QR để thực hiện bài kiểm tra" if url else "Vui lòng cập nhật liên kết Post-test")
            if url:
                try:
                    import qrcode
                    image = qrcode.make(url)
                    data = io.BytesIO()
                    image.save(data, format="PNG")
                    pix = QPixmap()
                    pix.loadFromData(data.getvalue())
                    self.qr.setPixmap(pix.scaled(280, 280, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                    self.qr.show()
                except Exception:
                    self.subtitle.setText(url)
        else:
            self.title.setText(scene.get("title", ""))
            self.subtitle.setText(self.program.organizer)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.escape_requested.emit()
        super().keyPressEvent(event)


def QColorWithAlpha(r, g, b, a):
    from PySide6.QtGui import QColor
    return QColor(r, g, b, a)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Điều khiển chương trình PowerPoint")
        self.resize(1180, 760)
        self.program = Program()
        self.program_path = ""
        self.scenes = []
        self.scene_index = -1
        self.ppt = PowerPointController()
        self.ppt_seen_running = False
        self.stage = StageWindow()
        self.stage.escape_requested.connect(self.stop_show)

        self.remote = RemoteControl()
        self.remote.next_requested.connect(self.next_scene)
        self.remote.previous_requested.connect(self.previous_scene)
        self.remote.start_requested.connect(self.start_show)
        self.remote.stop_requested.connect(self.stop_show)
        self.remote.start()

        self._build_ui()
        self._build_shortcuts()
        self._refresh_table()

        self.monitor = QTimer(self)
        self.monitor.timeout.connect(self._monitor_powerpoint)
        self.monitor.start(400)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        heading = QLabel("ĐIỀU KHIỂN CHƯƠNG TRÌNH")
        heading.setFont(QFont("Segoe UI", 20, QFont.Bold))
        root.addWidget(heading)

        form = QGridLayout()
        self.event_name = QLineEdit(self.program.event_name)
        self.organizer = QLineEdit()
        self.background = QLineEdit()
        self.logo = QLineEdit()
        self.discussion = QSpinBox()
        self.discussion.setRange(1, 240)
        self.discussion.setValue(20)
        self.post_url = QLineEdit()
        self.screen = QComboBox()
        self._load_screens()

        form.addWidget(QLabel("Tên chương trình"), 0, 0)
        form.addWidget(self.event_name, 0, 1, 1, 3)
        form.addWidget(QLabel("Đơn vị tổ chức"), 1, 0)
        form.addWidget(self.organizer, 1, 1, 1, 3)
        form.addWidget(QLabel("Background"), 2, 0)
        form.addWidget(self.background, 2, 1)
        bg_btn = QPushButton("Chọn ảnh…")
        bg_btn.clicked.connect(lambda: self._set_path(self.background, "Ảnh (*.png *.jpg *.jpeg *.bmp)"))
        form.addWidget(bg_btn, 2, 2)
        form.addWidget(QLabel("Logo"), 3, 0)
        form.addWidget(self.logo, 3, 1)
        logo_btn = QPushButton("Chọn logo…")
        logo_btn.clicked.connect(lambda: self._set_path(self.logo, "Ảnh (*.png *.jpg *.jpeg)"))
        form.addWidget(logo_btn, 3, 2)
        form.addWidget(QLabel("Màn hình sân khấu"), 2, 3)
        form.addWidget(self.screen, 2, 4)
        form.addWidget(QLabel("Thảo luận (phút)"), 3, 3)
        form.addWidget(self.discussion, 3, 4)
        form.addWidget(QLabel("Link Post-test"), 4, 0)
        form.addWidget(self.post_url, 4, 1, 1, 4)
        root.addLayout(form)

        toolbar = QHBoxLayout()
        for text, slot in [
            ("+ Thêm báo cáo viên", self.add_report),
            ("Sửa", self.edit_report),
            ("Xóa", self.delete_report),
            ("▲ Lên", lambda: self.move_report(-1)),
            ("▼ Xuống", lambda: self.move_report(1)),
        ]:
            button = QPushButton(text)
            button.clicked.connect(slot)
            toolbar.addWidget(button)
        toolbar.addStretch()
        root.addLayout(toolbar)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["STT", "Báo cáo viên", "Chuyên đề", "File PowerPoint", "Phút"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.doubleClicked.connect(self.edit_report)
        root.addWidget(self.table, 1)

        footer = QHBoxLayout()
        load_btn = QPushButton("Mở chương trình")
        load_btn.clicked.connect(self.load_program)
        save_btn = QPushButton("Lưu chương trình")
        save_btn.clicked.connect(self.save_program)
        preview_btn = QPushButton("Xem thử màn hình")
        preview_btn.clicked.connect(self.preview)
        remote_btn = QPushButton("Điều khiển từ xa…")
        remote_btn.clicked.connect(self.show_remote_dialog)
        self.previous_btn = QPushButton("◀ Phần trước")
        self.previous_btn.clicked.connect(self.previous_scene)
        self.start_btn = QPushButton("BẮT ĐẦU")
        self.start_btn.setObjectName("primary")
        self.start_btn.clicked.connect(self.start_show)
        self.next_btn = QPushButton("Phần tiếp ▶")
        self.next_btn.clicked.connect(self.next_scene)
        stop_btn = QPushButton("KẾT THÚC")
        stop_btn.setObjectName("danger")
        stop_btn.clicked.connect(self.stop_show)
        for button in [load_btn, save_btn, preview_btn, remote_btn, self.previous_btn, self.start_btn, self.next_btn, stop_btn]:
            footer.addWidget(button)
        root.addLayout(footer)

        self.status = QLabel("Sẵn sàng")
        self.statusBar().addWidget(self.status, 1)

    def _build_shortcuts(self):
        for shortcut, slot in [
            ("Ctrl+Right", self.next_scene),
            ("Ctrl+Left", self.previous_scene),
            ("F5", self.start_show),
            ("Escape", self.stop_show),
        ]:
            action = QAction(self)
            action.setShortcut(QKeySequence(shortcut))
            action.triggered.connect(slot)
            self.addAction(action)

    def _load_screens(self):
        self.screen.clear()
        screens = QApplication.screens()
        for index, screen in enumerate(screens, start=1):
            size = screen.geometry().size()
            self.screen.addItem(f"Màn hình {index} – {size.width()}×{size.height()}", screen)
        if len(screens) > 1:
            self.screen.setCurrentIndex(1)

    def _set_path(self, edit, file_filter):
        value = choose_file(self, "Chọn file", file_filter)
        if value:
            edit.setText(value)

    def _sync_program(self):
        self.program.event_name = self.event_name.text().strip()
        self.program.organizer = self.organizer.text().strip()
        self.program.background = self.background.text().strip()
        self.program.logo = self.logo.text().strip()
        self.program.discussion_minutes = self.discussion.value()
        self.program.post_test_url = self.post_url.text().strip()

    def _load_form(self):
        self.event_name.setText(self.program.event_name)
        self.organizer.setText(self.program.organizer)
        self.background.setText(self.program.background)
        self.logo.setText(self.program.logo)
        self.discussion.setValue(self.program.discussion_minutes)
        self.post_url.setText(self.program.post_test_url)
        self._refresh_table()

    def _refresh_table(self):
        self.table.setRowCount(len(self.program.reports))
        for row, report in enumerate(self.program.reports):
            values = [str(row + 1), report.name, report.topic, Path(report.ppt).name if report.ppt else "Chưa chọn", str(report.duration_minutes)]
            for column, value in enumerate(values):
                self.table.setItem(row, column, QTableWidgetItem(value))

    def selected_row(self):
        rows = self.table.selectionModel().selectedRows()
        return rows[0].row() if rows else -1

    def add_report(self):
        dialog = ReportDialog(self)
        if dialog.exec():
            self.program.reports.append(dialog.report())
            self._refresh_table()

    def edit_report(self):
        row = self.selected_row()
        if row < 0:
            return
        dialog = ReportDialog(self, self.program.reports[row])
        if dialog.exec():
            self.program.reports[row] = dialog.report()
            self._refresh_table()
            self.table.selectRow(row)

    def delete_report(self):
        row = self.selected_row()
        if row >= 0 and QMessageBox.question(self, "Xóa", "Xóa báo cáo viên đang chọn?") == QMessageBox.Yes:
            del self.program.reports[row]
            self._refresh_table()

    def move_report(self, delta):
        row = self.selected_row()
        target = row + delta
        if row < 0 or target < 0 or target >= len(self.program.reports):
            return
        self.program.reports[row], self.program.reports[target] = self.program.reports[target], self.program.reports[row]
        self._refresh_table()
        self.table.selectRow(target)

    def save_program(self):
        self._sync_program()
        path = self.program_path
        if not path:
            path, _ = QFileDialog.getSaveFileName(self, "Lưu chương trình", "chuong_trinh.json", "JSON (*.json)")
        if path:
            self.program.save(path)
            self.program_path = path
            self.status.setText(f"Đã lưu: {path}")

    def load_program(self):
        path, _ = QFileDialog.getOpenFileName(self, "Mở chương trình", "", "JSON (*.json)")
        if not path:
            return
        try:
            self.program = Program.load(path)
            self.program_path = path
            self._load_form()
            self.status.setText(f"Đã mở: {path}")
        except Exception as exc:
            QMessageBox.critical(self, "Không thể mở", str(exc))

    def _show_stage(self):
        screen = self.screen.currentData()
        if screen is None:
            screen = QApplication.primaryScreen()
        self.stage.set_program(self.program)
        self.stage.setGeometry(screen.geometry())
        self.stage.showFullScreen()
        self.stage.raise_()

    def preview(self):
        self._sync_program()
        self._show_stage()
        self.stage.show_scene({"type": "opening", "title": "CHÀO MỪNG QUÝ ĐẠI BIỂU"})

    def show_remote_dialog(self):
        dialog = RemoteDialog(self, self.remote)
        dialog.exec()

    def start_show(self):
        self._sync_program()
        errors = validate_program(self.program)
        if errors:
            QMessageBox.warning(self, "Chưa thể trình chiếu", "\n".join(errors))
            return
        self.scenes = self.program.scenes()
        self.scene_index = 0
        self._show_current_scene()

    def _show_current_scene(self):
        if not (0 <= self.scene_index < len(self.scenes)):
            return
        scene = self.scenes[self.scene_index]
        label = {
            "opening": "Mở đầu", "speaker": "Giới thiệu báo cáo viên",
            "powerpoint": "PowerPoint", "transition": "Chuyển tiếp",
            "discussion": "Thảo luận", "post_test": "Post-test", "closing": "Kết thúc",
        }.get(scene["type"], scene["type"])
        status_text = f"Phần {self.scene_index + 1}/{len(self.scenes)} – {label}"
        self.status.setText(status_text)
        self.remote.set_status(status_text)
        if scene["type"] == "powerpoint":
            self.stage.hide()
            self.ppt_seen_running = False
            try:
                self.ppt.start(scene["report"].ppt)
            except PowerPointError as exc:
                QMessageBox.critical(self, "Lỗi PowerPoint", str(exc))
                self._show_stage()
                self.stage.show_scene({"type": "transition", "title": "KHÔNG THỂ MỞ BÀI TRÌNH CHIẾU", "report": scene["report"]})
        else:
            self._show_stage()
            self.stage.show_scene(scene)

    def next_scene(self):
        if not self.scenes:
            return
        if self.ppt.is_running():
            self.ppt.close_presentation()
        if self.scene_index < len(self.scenes) - 1:
            self.scene_index += 1
            self._show_current_scene()

    def previous_scene(self):
        if not self.scenes:
            return
        if self.ppt.is_running():
            self.ppt.close_presentation()
        if self.scene_index > 0:
            self.scene_index -= 1
            self._show_current_scene()

    def _monitor_powerpoint(self):
        running = self.ppt.is_running()
        if running:
            self.ppt_seen_running = True
        elif self.ppt_seen_running:
            self.ppt_seen_running = False
            self.ppt.close_presentation()
            self.next_scene()

    def stop_show(self):
        self.ppt_seen_running = False
        self.ppt.close_presentation()
        self.stage.hide()
        self.scenes = []
        self.scene_index = -1
        self.status.setText("Đã kết thúc trình chiếu")
        self.remote.set_status("Đã kết thúc trình chiếu")

    def closeEvent(self, event):
        self.stage.close()
        self.ppt.shutdown()
        self.remote.stop()
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("PPT Event Controller")
    app.setStyleSheet(APP_STYLE)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
