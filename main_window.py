from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QTimer
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

from bulk_import import BulkImportDialog
from template_dialog import TemplateDialog
from core import Program, ProgramFileError, validate_program
from dialogs import ReportDialog, RemoteDialog, choose_file
from i18n import set_language, tr
from paths import app_dir
from powerpoint import PowerPointController, PowerPointError
from remote import RemoteControl
from settings import AppSettings
from settings_dialog import SettingsDialog
from stage import StageWindow
from timer_overlay import TimerOverlay

AUTOSAVE_PATH = app_dir() / "autosave.json"
AUTOSAVE_INTERVAL_MS = 30_000


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
        self.settings = AppSettings.load()
        set_language(self.settings.language)

        self.setWindowTitle(tr("Điều khiển chương trình PowerPoint"))
        self.resize(1180, 760)
        self.program = Program()
        self.program_path = ""
        self.scenes: list[dict] = []
        self.scene_index = -1
        self.ppt = PowerPointController()
        self.ppt_seen_running = False
        self._pending_ppt_hide_stage = False
        self.stage = StageWindow()
        self.stage.escape_requested.connect(self.stop_show)
        self.timer_overlay = TimerOverlay()

        self.remote = RemoteControl()
        self.remote.next_requested.connect(self.next_scene)
        self.remote.previous_requested.connect(self.previous_scene)
        self.remote.start_requested.connect(self.start_show)
        self.remote.stop_requested.connect(self.stop_show)
        self.remote.start(port=self.settings.remote_port)

        self._build_ui()
        self._build_shortcuts()
        self._refresh_table()
        self._offer_autosave_recovery()

        self.monitor = QTimer(self)
        self.monitor.timeout.connect(self._monitor_powerpoint)
        self.monitor.start(150)

        self.autosave_timer = QTimer(self)
        self.autosave_timer.timeout.connect(self._autosave)
        self.autosave_timer.start(AUTOSAVE_INTERVAL_MS)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        self.heading = QLabel(tr("ĐIỀU KHIỂN CHƯƠNG TRÌNH"))
        self.heading.setFont(QFont("Segoe UI", 20, QFont.Bold))
        root.addWidget(self.heading)

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

        self.label_event_name = QLabel(tr("Tên chương trình"))
        form.addWidget(self.label_event_name, 0, 0)
        form.addWidget(self.event_name, 0, 1, 1, 3)
        self.label_organizer = QLabel(tr("Đơn vị tổ chức"))
        form.addWidget(self.label_organizer, 1, 0)
        form.addWidget(self.organizer, 1, 1, 1, 3)
        self.label_background = QLabel(tr("Background"))
        form.addWidget(self.label_background, 2, 0)
        form.addWidget(self.background, 2, 1)
        self.bg_btn = QPushButton(tr("Chọn ảnh…"))
        self.bg_btn.clicked.connect(lambda: self._set_path(self.background, "Ảnh (*.png *.jpg *.jpeg *.bmp)"))
        form.addWidget(self.bg_btn, 2, 2)
        self.label_logo = QLabel(tr("Logo"))
        form.addWidget(self.label_logo, 3, 0)
        form.addWidget(self.logo, 3, 1)
        self.logo_btn = QPushButton(tr("Chọn logo…"))
        self.logo_btn.clicked.connect(lambda: self._set_path(self.logo, "Ảnh (*.png *.jpg *.jpeg)"))
        form.addWidget(self.logo_btn, 3, 2)
        self.label_screen = QLabel(tr("Màn hình sân khấu"))
        form.addWidget(self.label_screen, 2, 3)
        form.addWidget(self.screen, 2, 4)
        self.label_discussion = QLabel(tr("Thảo luận (phút)"))
        form.addWidget(self.label_discussion, 3, 3)
        form.addWidget(self.discussion, 3, 4)
        self.label_post_url = QLabel(tr("Link Post-test"))
        form.addWidget(self.label_post_url, 4, 0)
        form.addWidget(self.post_url, 4, 1, 1, 4)
        self.virtual_screen = QCheckBox(tr("Màn hình ảo (chỉ bật khi test, không có máy chiếu)"))
        self.virtual_screen.setToolTip(tr(
            "Khi bật: màn hình sân khấu hiện dưới dạng cửa sổ nhỏ để xem thử,\n"
            "không chiếm toàn màn hình — dùng khi không có máy chiếu/màn hình thứ 2 để test.\n"
            "Khi trình chiếu thật, hãy tắt mục này."
        ))
        form.addWidget(self.virtual_screen, 5, 3, 1, 2)
        self.show_timer = QCheckBox(tr("Hiện đồng hồ đếm giờ trên sân khấu"))
        self.show_timer.setChecked(True)
        form.addWidget(self.show_timer, 5, 0, 1, 3)

        self.opening_ppt = QLineEdit()
        self.opening_ppt.setReadOnly(True)
        self.label_opening_ppt = QLabel(tr("File khai mạc (PowerPoint, tùy chọn)"))
        form.addWidget(self.label_opening_ppt, 6, 0)
        form.addWidget(self.opening_ppt, 6, 1, 1, 2)
        self.opening_ppt_btn = QPushButton(tr("Chọn…"))
        self.opening_ppt_btn.clicked.connect(lambda: self._set_interface_ppt(self.opening_ppt))
        form.addWidget(self.opening_ppt_btn, 6, 3)
        self.opening_ppt_clear_btn = QPushButton(tr("Xóa"))
        self.opening_ppt_clear_btn.clicked.connect(lambda: self.opening_ppt.clear())
        form.addWidget(self.opening_ppt_clear_btn, 6, 4)

        self.closing_ppt = QLineEdit()
        self.closing_ppt.setReadOnly(True)
        self.label_closing_ppt = QLabel(tr("File kết thúc (PowerPoint, tùy chọn)"))
        form.addWidget(self.label_closing_ppt, 7, 0)
        form.addWidget(self.closing_ppt, 7, 1, 1, 2)
        self.closing_ppt_btn = QPushButton(tr("Chọn…"))
        self.closing_ppt_btn.clicked.connect(lambda: self._set_interface_ppt(self.closing_ppt))
        form.addWidget(self.closing_ppt_btn, 7, 3)
        self.closing_ppt_clear_btn = QPushButton(tr("Xóa"))
        self.closing_ppt_clear_btn.clicked.connect(lambda: self.closing_ppt.clear())
        form.addWidget(self.closing_ppt_clear_btn, 7, 4)
        root.addLayout(form)

        toolbar = QHBoxLayout()
        self.toolbar_buttons = []
        for text, slot in [
            ("+ Thêm báo cáo viên", self.add_report),
            ("Nhập nhiều file PowerPoint…", self.bulk_import),
            ("Sửa", self.edit_report),
            ("Xóa", self.delete_report),
            ("▲ Lên", lambda: self.move_report(-1)),
            ("▼ Xuống", lambda: self.move_report(1)),
        ]:
            button = QPushButton(tr(text))
            button.clicked.connect(slot)
            toolbar.addWidget(button)
            self.toolbar_buttons.append((button, text))
        toolbar.addStretch()
        root.addLayout(toolbar)

        self.table = QTableWidget(0, 5)
        self.table_headers = ["STT", "Báo cáo viên", "Chuyên đề", "File PowerPoint", "Phút"]
        self.table.setHorizontalHeaderLabels([tr(h) for h in self.table_headers])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setDragDropMode(QTableWidget.InternalMove)
        self.table.setDragDropOverwriteMode(False)
        self.table.doubleClicked.connect(self.edit_report)
        self.table.model().rowsMoved.connect(self._on_rows_dragged)
        root.addWidget(self.table, 1)

        footer = QHBoxLayout()
        self.load_btn = QPushButton(tr("Mở chương trình"))
        self.load_btn.clicked.connect(self.load_program)
        self.save_btn = QPushButton(tr("Lưu chương trình"))
        self.save_btn.clicked.connect(self.save_program)
        self.template_btn = QPushButton(tr("Mẫu chương trình…"))
        self.template_btn.clicked.connect(self.show_template_dialog)
        self.preview_btn = QPushButton(tr("Xem thử màn hình"))
        self.preview_btn.clicked.connect(self.preview)
        self.remote_btn = QPushButton(tr("Điều khiển từ xa…"))
        self.remote_btn.clicked.connect(self.show_remote_dialog)
        self.settings_btn = QPushButton(tr("Cài đặt…"))
        self.settings_btn.clicked.connect(self.show_settings_dialog)
        self.previous_btn = QPushButton(tr("◀ Phần trước"))
        self.previous_btn.clicked.connect(self.previous_scene)
        self.start_btn = QPushButton(tr("BẮT ĐẦU"))
        self.start_btn.setObjectName("primary")
        self.start_btn.clicked.connect(self.start_show)
        self.next_btn = QPushButton(tr("Phần tiếp ▶"))
        self.next_btn.clicked.connect(self.next_scene)
        self.stop_btn = QPushButton(tr("KẾT THÚC"))
        self.stop_btn.setObjectName("danger")
        self.stop_btn.clicked.connect(self.stop_show)
        for button in [
            self.load_btn, self.save_btn, self.template_btn, self.preview_btn, self.remote_btn, self.settings_btn,
            self.previous_btn, self.start_btn, self.next_btn, self.stop_btn,
        ]:
            footer.addWidget(button)
        root.addLayout(footer)

        self.status = QLabel(tr("Sẵn sàng"))
        self.statusBar().addWidget(self.status, 1)
        self.remote_status = QLabel()
        self.remote_status.setStyleSheet("color: #64748b;")
        self.refresh_remote_status()
        self.statusBar().addPermanentWidget(self.remote_status)

    def refresh_remote_status(self) -> None:
        port = self.remote.server.server_address[1] if self.remote.server else None
        text = tr("📡 Điều khiển từ xa: cổng {port}").format(port=port) if port else tr("📡 Điều khiển từ xa: chưa bật")
        self.remote_status.setText(text)

    def retranslate_visible_texts(self) -> None:
        """Cập nhật lại các nhãn tĩnh dễ thấy nhất sau khi đổi ngôn ngữ (không cần khởi động lại)."""
        self.setWindowTitle(tr("Điều khiển chương trình PowerPoint"))
        self.heading.setText(tr("ĐIỀU KHIỂN CHƯƠNG TRÌNH"))
        self.label_event_name.setText(tr("Tên chương trình"))
        self.label_organizer.setText(tr("Đơn vị tổ chức"))
        self.label_background.setText(tr("Background"))
        self.bg_btn.setText(tr("Chọn ảnh…"))
        self.label_logo.setText(tr("Logo"))
        self.logo_btn.setText(tr("Chọn logo…"))
        self.label_screen.setText(tr("Màn hình sân khấu"))
        self.label_discussion.setText(tr("Thảo luận (phút)"))
        self.label_post_url.setText(tr("Link Post-test"))
        self.virtual_screen.setText(tr("Màn hình ảo (chỉ bật khi test, không có máy chiếu)"))
        self.show_timer.setText(tr("Hiện đồng hồ đếm giờ trên sân khấu"))
        self.label_opening_ppt.setText(tr("File khai mạc (PowerPoint, tùy chọn)"))
        self.label_closing_ppt.setText(tr("File kết thúc (PowerPoint, tùy chọn)"))
        for button in (self.opening_ppt_btn, self.closing_ppt_btn):
            button.setText(tr("Chọn…"))
        for button in (self.opening_ppt_clear_btn, self.closing_ppt_clear_btn):
            button.setText(tr("Xóa"))
        for button, key in self.toolbar_buttons:
            button.setText(tr(key))
        self.table.setHorizontalHeaderLabels([tr(h) for h in self.table_headers])
        self.load_btn.setText(tr("Mở chương trình"))
        self.save_btn.setText(tr("Lưu chương trình"))
        self.template_btn.setText(tr("Mẫu chương trình…"))
        self.preview_btn.setText(tr("Xem thử màn hình"))
        self.remote_btn.setText(tr("Điều khiển từ xa…"))
        self.settings_btn.setText(tr("Cài đặt…"))
        self.previous_btn.setText(tr("◀ Phần trước"))
        self.start_btn.setText(tr("BẮT ĐẦU"))
        self.next_btn.setText(tr("Phần tiếp ▶"))
        self.stop_btn.setText(tr("KẾT THÚC"))
        self.refresh_remote_status()

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
        preferred = self.settings.preferred_screen_index
        if 0 <= preferred < len(screens):
            self.screen.setCurrentIndex(preferred)
        elif len(screens) > 1:
            self.screen.setCurrentIndex(1)

    def _set_path(self, edit, file_filter):
        value = choose_file(self, tr("Chọn file"), file_filter)
        if value:
            edit.setText(value)

    def _set_interface_ppt(self, edit):
        value = choose_file(self, tr("Chọn file"), "PowerPoint (*.ppt *.pptx *.pptm *.pps *.ppsx)")
        if value:
            edit.setText(value)

    def bulk_import(self):
        self._sync_program()
        dialog = BulkImportDialog(self, self.program)
        if dialog.exec():
            self._load_form()

    def _sync_program(self):
        self.program.event_name = self.event_name.text().strip()
        self.program.organizer = self.organizer.text().strip()
        self.program.background = self.background.text().strip()
        self.program.logo = self.logo.text().strip()
        self.program.discussion_minutes = self.discussion.value()
        self.program.post_test_url = self.post_url.text().strip()
        self.program.opening_ppt = self.opening_ppt.text().strip()
        self.program.closing_ppt = self.closing_ppt.text().strip()

    def _load_form(self):
        self.event_name.setText(self.program.event_name)
        self.organizer.setText(self.program.organizer)
        self.background.setText(self.program.background)
        self.logo.setText(self.program.logo)
        self.discussion.setValue(self.program.discussion_minutes)
        self.post_url.setText(self.program.post_test_url)
        self.opening_ppt.setText(self.program.opening_ppt)
        self.closing_ppt.setText(self.program.closing_ppt)
        self._refresh_table()

    def _refresh_table(self):
        self.table.setRowCount(len(self.program.reports))
        for row, report in enumerate(self.program.reports):
            values = [
                str(row + 1),
                report.name,
                report.topic,
                Path(report.ppt).name if report.ppt else tr("Chưa chọn"),
                str(report.duration_minutes),
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column == 0:
                    item.setData(Qt.UserRole, report)
                self.table.setItem(row, column, item)

    def selected_row(self):
        rows = self.table.selectionModel().selectedRows()
        return rows[0].row() if rows else -1

    def _on_rows_dragged(self, *_args):
        """Đồng bộ lại thứ tự self.program.reports sau khi người dùng kéo-thả đổi vị trí dòng."""
        new_order = []
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            report = item.data(Qt.UserRole) if item else None
            if report is not None:
                new_order.append(report)
        if len(new_order) == len(self.program.reports):
            self.program.reports = new_order
        self._refresh_table()

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
        if row >= 0 and self._confirm(tr("Xóa"), tr("Xóa báo cáo viên đang chọn?")):
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

    def _offer_autosave_recovery(self):
        if not AUTOSAVE_PATH.is_file():
            return
        try:
            recovered = Program.load(str(AUTOSAVE_PATH))
        except ProgramFileError:
            AUTOSAVE_PATH.unlink(missing_ok=True)
            return
        if not self._confirm(
            tr("Khôi phục dữ liệu"),
            tr(
                "Phát hiện dữ liệu tự động lưu từ lần chạy trước (có thể do ứng dụng bị đóng "
                "đột ngột). Khôi phục lại chương trình đó?"
            ),
        ):
            AUTOSAVE_PATH.unlink(missing_ok=True)
            return
        self.program = recovered
        self._load_form()
        self.status.setText(tr("Đã khôi phục dữ liệu tự động lưu."))

    def _autosave(self):
        self._sync_program()
        if not self.program.event_name.strip() and not self.program.reports:
            return
        try:
            self.program.save(str(AUTOSAVE_PATH))
        except ProgramFileError:
            pass

    def _clear_autosave(self):
        AUTOSAVE_PATH.unlink(missing_ok=True)

    def save_program(self):
        self._sync_program()
        path = self.program_path
        if not path:
            path, _ = QFileDialog.getSaveFileName(self, tr("Lưu chương trình"), "chuong_trinh.json", "JSON (*.json)")
        if not path:
            return
        try:
            self.program.save(path)
        except ProgramFileError as exc:
            QMessageBox.critical(self, tr("Không thể lưu"), str(exc))
            return
        self.program_path = path
        self._clear_autosave()
        self.status.setText(tr("Đã lưu: {path}").format(path=path))

    def load_program(self):
        if self.program.reports and not self._confirm(
            tr("Mở chương trình khác"),
            tr("Dữ liệu báo cáo viên hiện tại chưa được lưu sẽ bị thay thế. Tiếp tục?"),
        ):
            return
        path, _ = QFileDialog.getOpenFileName(self, tr("Mở chương trình"), "", "JSON (*.json)")
        if not path:
            return
        try:
            self.program = Program.load(path)
        except ProgramFileError as exc:
            QMessageBox.critical(self, tr("Không thể mở"), str(exc))
            return
        self.program_path = path
        self._load_form()
        self._clear_autosave()
        self.status.setText(tr("Đã mở: {path}").format(path=path))

    def show_template_dialog(self):
        self._sync_program()
        dialog = TemplateDialog(self, self.program)
        if dialog.exec() and dialog.loaded_program is not None:
            self.program = dialog.loaded_program
            self.program_path = ""
            self._load_form()
            self._clear_autosave()
            self.status.setText(tr("Đã tải mẫu chương trình."))

    def _show_stage(self):
        screen = self.screen.currentData()
        if screen is None:
            screen = QApplication.primaryScreen()
        self.stage.set_program(self.program)
        if self.virtual_screen.isChecked():
            self.stage.set_simulation_mode(True)
            self.stage.setWindowTitle(tr("Màn hình sân khấu (ẢO – chỉ dùng để test)"))
            self.stage.resize(960, 540)
            geometry = screen.geometry()
            self.stage.move(geometry.x() + 40, geometry.y() + 40)
            self.stage.show()
        else:
            self.stage.set_simulation_mode(False)
            self.stage.setWindowTitle(tr("Màn hình trình chiếu"))
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

    def show_settings_dialog(self):
        dialog = SettingsDialog(self, self.settings, self.remote, self.screen)
        dialog.exec()

    def _confirm(self, title: str, question: str) -> bool:
        return QMessageBox.question(self, title, question) == QMessageBox.Yes

    def start_show(self):
        if self.scenes and not self._confirm(
            tr("Bắt đầu lại"), tr("Chương trình đang chạy. Bắt đầu lại từ đầu?")
        ):
            return
        self._sync_program()
        errors = validate_program(self.program)
        if errors:
            QMessageBox.warning(self, tr("Chưa thể trình chiếu"), "\n".join(errors))
            return
        self.scenes = self.program.scenes()
        self.scene_index = 0
        self._autosave()
        self._show_current_scene()

    def _show_current_scene(self):
        if not (0 <= self.scene_index < len(self.scenes)):
            return
        scene = self.scenes[self.scene_index]
        label = self._scene_label(scene)
        status_text = tr("Phần {index}/{total} – {label}").format(
            index=self.scene_index + 1, total=len(self.scenes), label=label
        )
        self.status.setText(status_text)
        self.remote.set_status(status_text)
        self._update_timer_overlay(scene)
        if scene["type"] == "powerpoint":
            # Giữ màn hình sân khấu hiển thị (không hide() ngay) trong lúc PowerPoint đang mở —
            # chỉ ẩn đi khi PowerPoint đã thật sự chạy (xem _monitor_powerpoint), để tránh
            # lộ desktop trong khoảng trống giữa lúc ẩn app và lúc PowerPoint kịp toàn màn hình.
            self.ppt_seen_running = False
            self._pending_ppt_hide_stage = True
            try:
                self.ppt.start(scene["report"].ppt)
            except PowerPointError as exc:
                self._pending_ppt_hide_stage = False
                QMessageBox.critical(self, tr("Lỗi PowerPoint"), str(exc))
                self._show_stage()
                self.stage.show_scene({"type": "transition", "title": "KHÔNG THỂ MỞ BÀI TRÌNH CHIẾU", "report": scene["report"]})
        else:
            self._pending_ppt_hide_stage = False
            self._show_stage()
            self.stage.show_scene(scene)

    def _scene_label(self, scene: dict) -> str:
        if scene["type"] == "powerpoint" and scene.get("interface_kind"):
            return tr("Khai mạc (PowerPoint)") if scene["interface_kind"] == "opening" else tr("Kết thúc (PowerPoint)")
        return tr(SCENE_LABELS.get(scene["type"], scene["type"]))

    def _update_timer_overlay(self, scene: dict) -> None:
        if not self.show_timer.isChecked():
            self.timer_overlay.stop()
            return
        screen = self.screen.currentData() or QApplication.primaryScreen()
        if scene["type"] == "powerpoint" and scene["report"].duration_minutes > 0:
            self.timer_overlay.start(scene["report"].duration_minutes, screen.geometry())
        elif scene["type"] == "discussion":
            self.timer_overlay.start(scene["duration_minutes"], screen.geometry())
        else:
            self.timer_overlay.stop()

    def _prepare_stage_for_scene(self, scene: dict) -> None:
        """Hiện sẵn nội dung của scene sắp tới lên màn hình sân khấu trước khi đóng
        PowerPoint hiện tại, để lúc PowerPoint đóng thì bên dưới đã là app thay vì desktop."""
        if scene["type"] == "powerpoint":
            return
        self._pending_ppt_hide_stage = False
        self._show_stage()
        self.stage.show_scene(scene)
        QApplication.processEvents()

    def next_scene(self):
        if not self.scenes or self.scene_index >= len(self.scenes) - 1:
            return
        if self.ppt.is_running():
            self._prepare_stage_for_scene(self.scenes[self.scene_index + 1])
            self.ppt.close_presentation()
            # Vừa chủ động đóng PowerPoint theo lệnh người dùng — không phải do báo cáo
            # viên tự thoát — nên phải hủy cờ này, tránh _monitor_powerpoint hiểu nhầm
            # thành "PowerPoint vừa tự kết thúc" và tự ý bấm tiếp thêm 1 lần nữa.
            self.ppt_seen_running = False
        self.scene_index += 1
        self._show_current_scene()

    def previous_scene(self):
        if not self.scenes or self.scene_index <= 0:
            return
        if self.ppt.is_running():
            self._prepare_stage_for_scene(self.scenes[self.scene_index - 1])
            self.ppt.close_presentation()
            self.ppt_seen_running = False
        self.scene_index -= 1
        self._show_current_scene()

    def _monitor_powerpoint(self):
        running = self.ppt.is_running()
        if running:
            if self._pending_ppt_hide_stage:
                self.stage.hide()
                self._pending_ppt_hide_stage = False
            self.ppt_seen_running = True
        elif self.ppt_seen_running:
            self.ppt_seen_running = False
            if self.scene_index < len(self.scenes) - 1:
                self._prepare_stage_for_scene(self.scenes[self.scene_index + 1])
            self.ppt.close_presentation()
            self.next_scene()

    def stop_show(self):
        if self.scenes and not self._confirm(
            tr("Kết thúc trình chiếu"), tr("Bạn có chắc muốn kết thúc trình chiếu hiện tại?")
        ):
            return
        self.ppt_seen_running = False
        self._pending_ppt_hide_stage = False
        self.ppt.close_presentation()
        self.stage.hide()
        self.timer_overlay.stop()
        self.scenes = []
        self.scene_index = -1
        self.status.setText(tr("Đã kết thúc trình chiếu"))
        self.remote.set_status(tr("Đã kết thúc trình chiếu"))

    def closeEvent(self, event):
        if self.scenes and not self._confirm(
            tr("Đóng ứng dụng"), tr("Chương trình đang trình chiếu. Đóng ứng dụng sẽ dừng toàn bộ. Tiếp tục?")
        ):
            event.ignore()
            return
        self.stage.close()
        self.timer_overlay.close()
        self.ppt.shutdown()
        self.remote.stop()
        self._clear_autosave()
        event.accept()
