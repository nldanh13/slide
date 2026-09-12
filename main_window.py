from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtGui import QAction, QFont, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
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

from core import Program, ProgramFileError, validate_program
from dialogs import ReportDialog, RemoteDialog, choose_file
from powerpoint import PowerPointController, PowerPointError
from remote import RemoteControl
from stage import StageWindow


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

SCENE_LABELS = {
    "opening": "Mở đầu",
    "speaker": "Giới thiệu báo cáo viên",
    "powerpoint": "PowerPoint",
    "transition": "Chuyển tiếp",
    "discussion": "Thảo luận",
    "post_test": "Post-test",
    "closing": "Kết thúc",
}


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Điều khiển chương trình PowerPoint")
        self.resize(1180, 760)
        self.program = Program()
        self.program_path = ""
        self.scenes: list[dict] = []
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
        self.virtual_screen = QCheckBox("Màn hình ảo (chỉ bật khi test, không có máy chiếu)")
        self.virtual_screen.setToolTip(
            "Khi bật: màn hình sân khấu hiện dưới dạng cửa sổ nhỏ để xem thử,\n"
            "không chiếm toàn màn hình — dùng khi không có máy chiếu/màn hình thứ 2 để test.\n"
            "Khi trình chiếu thật, hãy tắt mục này."
        )
        form.addWidget(self.virtual_screen, 5, 3, 1, 2)
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
        self.remote_status = QLabel(self._remote_status_text())
        self.remote_status.setStyleSheet("color: #64748b;")
        self.statusBar().addPermanentWidget(self.remote_status)

    def _remote_status_text(self) -> str:
        port = self.remote.server.server_address[1] if self.remote.server else None
        return f"📡 Điều khiển từ xa: cổng {port}" if port else "📡 Điều khiển từ xa: chưa bật"

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
        if not path:
            return
        try:
            self.program.save(path)
        except ProgramFileError as exc:
            QMessageBox.critical(self, "Không thể lưu", str(exc))
            return
        self.program_path = path
        self.status.setText(f"Đã lưu: {path}")

    def load_program(self):
        if self.program.reports and not self._confirm(
            "Mở chương trình khác",
            "Dữ liệu báo cáo viên hiện tại chưa được lưu sẽ bị thay thế. Tiếp tục?",
        ):
            return
        path, _ = QFileDialog.getOpenFileName(self, "Mở chương trình", "", "JSON (*.json)")
        if not path:
            return
        try:
            self.program = Program.load(path)
        except ProgramFileError as exc:
            QMessageBox.critical(self, "Không thể mở", str(exc))
            return
        self.program_path = path
        self._load_form()
        self.status.setText(f"Đã mở: {path}")

    def _show_stage(self):
        screen = self.screen.currentData()
        if screen is None:
            screen = QApplication.primaryScreen()
        self.stage.set_program(self.program)
        if self.virtual_screen.isChecked():
            self.stage.set_simulation_mode(True)
            self.stage.setWindowTitle("Màn hình sân khấu (ẢO – chỉ dùng để test)")
            self.stage.resize(960, 540)
            geometry = screen.geometry()
            self.stage.move(geometry.x() + 40, geometry.y() + 40)
            self.stage.show()
        else:
            self.stage.set_simulation_mode(False)
            self.stage.setWindowTitle("Màn hình trình chiếu")
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

    def _confirm(self, title: str, question: str) -> bool:
        return QMessageBox.question(self, title, question) == QMessageBox.Yes

    def start_show(self):
        if self.scenes and not self._confirm(
            "Bắt đầu lại", "Chương trình đang chạy. Bắt đầu lại từ đầu?"
        ):
            return
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
        label = SCENE_LABELS.get(scene["type"], scene["type"])
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
        if self.scenes and not self._confirm(
            "Kết thúc trình chiếu", "Bạn có chắc muốn kết thúc trình chiếu hiện tại?"
        ):
            return
        self.ppt_seen_running = False
        self.ppt.close_presentation()
        self.stage.hide()
        self.scenes = []
        self.scene_index = -1
        self.status.setText("Đã kết thúc trình chiếu")
        self.remote.set_status("Đã kết thúc trình chiếu")

    def closeEvent(self, event):
        if self.scenes and not self._confirm(
            "Đóng ứng dụng", "Chương trình đang trình chiếu. Đóng ứng dụng sẽ dừng toàn bộ. Tiếp tục?"
        ):
            event.ignore()
            return
        self.stage.close()
        self.ppt.shutdown()
        self.remote.stop()
        event.accept()
