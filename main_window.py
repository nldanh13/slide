from __future__ import annotations

import re
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QFont, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from backup_dialog import BackupDialog
from backups import create_backup
from bulk_import import classify_file, guess_report_name
from template_dialog import TemplateDialog
from core import Program, ProgramFileError, Report, validate_program
from dialogs import ReportDialog, RemoteDialog, choose_file
from export_schedule import export_schedule_pdf
from i18n import set_language, tr
from interface_media_dialog import InterfaceMediaDialog
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
QWidget { font-family: "Segoe UI"; font-size: 10pt; color: #162033; background: #f4f7fb; }
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
QMenu { background: #ffffff; color: #162033; border: 1px solid #ccd5e2; }
QMenu::item { padding: 6px 24px; background: transparent; }
QMenu::item:selected { background: #d8e3f3; }
QMenu::separator { height: 1px; background: #e5eaf1; margin: 4px 0; }
QGroupBox {
    border: 1px solid #dbe3ee; border-radius: 8px; margin-top: 14px;
    padding: 14px 10px 10px 10px; font-weight: 600; background: #ffffff;
}
QGroupBox::title {
    subcontrol-origin: margin; subcontrol-position: top left;
    left: 10px; padding: 0 6px; color: #075985; background: #f4f7fb;
}
QPushButton#iconSmall { padding: 4px 8px; min-width: 0; }
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

PPT_FILTER = "PowerPoint (*.ppt *.pptx *.pptm *.pps *.ppsx)"
IMAGE_FILTER = "Ảnh (*.png *.jpg *.jpeg *.bmp)"

# (tên trường trong Program, nhãn hiển thị, loại file) cho từng phần giao diện có thể
# gán riêng file/ảnh — hiển thị trong bảng "Giao diện chương trình" ở cửa sổ chính.
INTERFACE_SLOTS = [
    ("opening_ppt", "Mở đầu (PowerPoint)", "ppt"),
    ("background", "Nền mặc định (ảnh)", "image"),
    ("discussion_image", "Thảo luận (ảnh riêng)", "image"),
    ("post_test_image", "Post-test (ảnh riêng)", "image"),
    ("closing_ppt", "Kết thúc (PowerPoint)", "ppt"),
    ("closing_image", "Kết thúc (ảnh riêng)", "image"),
]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = AppSettings.load()
        set_language(self.settings.language)

        self.setWindowTitle(tr("Điều khiển chương trình PowerPoint"))
        self.resize(1180, 900)
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

        self.info_group = QGroupBox(tr("Thông tin chương trình"))
        form = QGridLayout(self.info_group)
        self.event_name = QLineEdit(self.program.event_name)
        self.organizer = QLineEdit()
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
        self.label_logo = QLabel(tr("Logo"))
        form.addWidget(self.label_logo, 2, 0)
        form.addWidget(self.logo, 2, 1)
        self.logo_btn = QPushButton(tr("Chọn logo…"))
        self.logo_btn.clicked.connect(lambda: self._set_path(self.logo, "Ảnh (*.png *.jpg *.jpeg)"))
        form.addWidget(self.logo_btn, 2, 2)
        self.label_screen = QLabel(tr("Màn hình sân khấu"))
        form.addWidget(self.label_screen, 2, 3)
        form.addWidget(self.screen, 2, 4)
        self.label_discussion = QLabel(tr("Thảo luận (phút)"))
        form.addWidget(self.label_discussion, 3, 0)
        form.addWidget(self.discussion, 3, 1)
        self.label_post_url = QLabel(tr("Link Post-test"))
        form.addWidget(self.label_post_url, 4, 0)
        form.addWidget(self.post_url, 4, 1, 1, 4)
        self.virtual_screen = QCheckBox(tr("Màn hình ảo (chỉ bật khi test, không có máy chiếu)"))
        self.virtual_screen.setToolTip(tr(
            "Khi bật: màn hình sân khấu hiện dưới dạng cửa sổ nhỏ để xem thử,\n"
            "không chiếm toàn màn hình — dùng khi không có máy chiếu/màn hình thứ 2 để test.\n"
            "Khi trình chiếu thật, hãy tắt mục này."
        ))
        form.addWidget(self.virtual_screen, 5, 0, 1, 2)
        self.show_timer = QCheckBox(tr("Hiện đồng hồ đếm giờ trên sân khấu"))
        self.show_timer.setChecked(True)
        form.addWidget(self.show_timer, 5, 2, 1, 3)
        root.addWidget(self.info_group)

        self.speakers_group = QGroupBox(tr("Báo cáo viên"))
        speakers_layout = QVBoxLayout(self.speakers_group)

        toolbar = QHBoxLayout()
        self.toolbar_buttons = []
        for text, slot in [
            ("Thêm báo cáo viên / Nhập file…", self.import_files),
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
        speakers_layout.addLayout(toolbar)

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
        speakers_layout.addWidget(self.table, 1)
        root.addWidget(self.speakers_group, 1)

        self.interface_group = QGroupBox(tr("Giao diện chương trình"))
        interface_layout = QVBoxLayout(self.interface_group)

        self.interface_table = QTableWidget(len(INTERFACE_SLOTS), 3)
        self.interface_headers = ["Phần", "File", ""]
        self.interface_table.setHorizontalHeaderLabels([tr(h) for h in self.interface_headers])
        self.interface_table.verticalHeader().setVisible(False)
        self.interface_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.interface_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.interface_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.interface_table.setSelectionMode(QTableWidget.NoSelection)
        self.interface_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.interface_table.verticalHeader().setDefaultSectionSize(30)
        self.interface_table.setMinimumHeight(240)
        self.interface_table.setMaximumHeight(240)
        self._interface_action_widgets = []
        for row, (field, label_key, kind) in enumerate(INTERFACE_SLOTS):
            label_item = QTableWidgetItem(tr(label_key))
            self.interface_table.setItem(row, 0, label_item)
            self.interface_table.setItem(row, 1, QTableWidgetItem(""))

            action_box = QWidget()
            action_row = QHBoxLayout(action_box)
            action_row.setContentsMargins(4, 2, 4, 2)
            action_row.setSpacing(4)
            choose_btn = QPushButton(tr("Chọn…"))
            choose_btn.setMinimumWidth(78)
            choose_btn.clicked.connect(
                lambda _checked=False, f=field, k=kind: self._choose_interface_file(f, k)
            )
            clear_btn = QPushButton("✕")
            clear_btn.setObjectName("iconSmall")
            clear_btn.setFixedWidth(28)
            clear_btn.setToolTip(tr("Xóa"))
            clear_btn.clicked.connect(lambda _checked=False, f=field: self._clear_interface_file(f))
            action_row.addWidget(choose_btn)
            action_row.addWidget(clear_btn)
            self.interface_table.setCellWidget(row, 2, action_box)
            self._interface_action_widgets.append((choose_btn, clear_btn))
        self._refresh_interface_table()
        interface_layout.addWidget(self.interface_table)

        self.interface_media_btn = QPushButton(tr("Cấu hình slide nâng cao (từ file chương trình tổng)…"))
        self.interface_media_btn.clicked.connect(self.show_interface_media_dialog)
        interface_layout.addWidget(self.interface_media_btn)
        root.addWidget(self.interface_group)

        footer = QHBoxLayout()
        self.file_menu_btn = QPushButton(tr("Quản lý chương trình ▾"))
        file_menu = QMenu(self.file_menu_btn)
        self.load_action = file_menu.addAction(tr("Mở chương trình"))
        self.load_action.triggered.connect(self.load_program)
        self.save_action = file_menu.addAction(tr("Lưu chương trình"))
        self.save_action.triggered.connect(self.save_program)
        file_menu.addSeparator()
        self.backup_action = file_menu.addAction(tr("Khôi phục sao lưu…"))
        self.backup_action.triggered.connect(self.show_backup_dialog)
        self.template_action = file_menu.addAction(tr("Mẫu chương trình…"))
        self.template_action.triggered.connect(self.show_template_dialog)
        file_menu.addSeparator()
        self.export_pdf_action = file_menu.addAction(tr("Xuất lịch trình (PDF)…"))
        self.export_pdf_action.triggered.connect(self.export_schedule)
        self.file_menu_btn.setMenu(file_menu)

        self.tools_menu_btn = QPushButton(tr("Công cụ ▾"))
        tools_menu = QMenu(self.tools_menu_btn)
        self.preview_action = tools_menu.addAction(tr("Xem thử màn hình"))
        self.preview_action.triggered.connect(self.preview)
        self.remote_action = tools_menu.addAction(tr("Điều khiển từ xa…"))
        self.remote_action.triggered.connect(self.show_remote_dialog)
        self.settings_action = tools_menu.addAction(tr("Cài đặt…"))
        self.settings_action.triggered.connect(self.show_settings_dialog)
        self.tools_menu_btn.setMenu(tools_menu)

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
            self.file_menu_btn, self.tools_menu_btn,
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
        self.label_logo.setText(tr("Logo"))
        self.logo_btn.setText(tr("Chọn logo…"))
        self.label_screen.setText(tr("Màn hình sân khấu"))
        self.label_discussion.setText(tr("Thảo luận (phút)"))
        self.label_post_url.setText(tr("Link Post-test"))
        self.virtual_screen.setText(tr("Màn hình ảo (chỉ bật khi test, không có máy chiếu)"))
        self.show_timer.setText(tr("Hiện đồng hồ đếm giờ trên sân khấu"))
        self.info_group.setTitle(tr("Thông tin chương trình"))
        self.speakers_group.setTitle(tr("Báo cáo viên"))
        self.interface_group.setTitle(tr("Giao diện chương trình"))
        for button, key in self.toolbar_buttons:
            button.setText(tr(key))
        self.table.setHorizontalHeaderLabels([tr(h) for h in self.table_headers])
        self.interface_table.setHorizontalHeaderLabels([tr(h) for h in self.interface_headers])
        for row, (_field, label_key, _kind) in enumerate(INTERFACE_SLOTS):
            self.interface_table.item(row, 0).setText(tr(label_key))
        for choose_btn, clear_btn in self._interface_action_widgets:
            choose_btn.setText(tr("Chọn…"))
            clear_btn.setToolTip(tr("Xóa"))
        self._refresh_interface_table()
        self.interface_media_btn.setText(tr("Cấu hình slide nâng cao (từ file chương trình tổng)…"))
        self.file_menu_btn.setText(tr("Quản lý chương trình ▾"))
        self.load_action.setText(tr("Mở chương trình"))
        self.save_action.setText(tr("Lưu chương trình"))
        self.backup_action.setText(tr("Khôi phục sao lưu…"))
        self.template_action.setText(tr("Mẫu chương trình…"))
        self.export_pdf_action.setText(tr("Xuất lịch trình (PDF)…"))
        self.tools_menu_btn.setText(tr("Công cụ ▾"))
        self.preview_action.setText(tr("Xem thử màn hình"))
        self.remote_action.setText(tr("Điều khiển từ xa…"))
        self.settings_action.setText(tr("Cài đặt…"))
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

    def import_files(self):
        """Nút nhập duy nhất: chọn 1 hoặc nhiều file PowerPoint/ảnh cùng lúc, ứng dụng đoán
        vai trò theo tên file và áp dụng ngay — báo cáo viên thêm vào bảng bên dưới (bấm
        Sửa để bổ sung chi tiết), file/ảnh giao diện điền vào bảng "Giao diện chương trình"."""
        paths, _ = QFileDialog.getOpenFileNames(
            self, tr("Chọn file báo cáo viên hoặc file/ảnh giao diện"), "",
            f"{tr('PowerPoint & Ảnh')} (*.ppt *.pptx *.pptm *.pps *.ppsx *.png *.jpg *.jpeg *.bmp)",
        )
        if not paths:
            return
        for path in paths:
            role = classify_file(path)
            if role == "speaker":
                self.program.reports.append(Report(name=guess_report_name(path), ppt=path))
            elif role == "opening":
                self.program.opening_ppt = path
            elif role == "closing":
                self.program.closing_ppt = path
            elif role == "background":
                self.program.background = path
            elif role == "discussion":
                self.program.discussion_image = path
            elif role == "post_test":
                self.program.post_test_image = path
            elif role == "closing_image":
                self.program.closing_image = path
        self._refresh_table()
        self._refresh_interface_table()
        self.status.setText(
            tr("Đã nhập {count} file — kiểm tra vai trò ở bảng bên dưới, bấm Sửa để bổ sung chi tiết.")
            .format(count=len(paths))
        )

    def _refresh_interface_table(self):
        for row, (field, _label_key, _kind) in enumerate(INTERFACE_SLOTS):
            value = getattr(self.program, field)
            text = Path(value).name if value else tr("Chưa chọn")
            self.interface_table.item(row, 1).setText(text)

    def _choose_interface_file(self, field: str, kind: str):
        file_filter = PPT_FILTER if kind == "ppt" else IMAGE_FILTER
        value = choose_file(self, tr("Chọn file"), file_filter)
        if value:
            setattr(self.program, field, value)
            self._refresh_interface_table()

    def _clear_interface_file(self, field: str):
        setattr(self.program, field, "")
        self._refresh_interface_table()

    def _sync_program(self):
        self.program.event_name = self.event_name.text().strip()
        self.program.organizer = self.organizer.text().strip()
        self.program.logo = self.logo.text().strip()
        self.program.discussion_minutes = self.discussion.value()
        self.program.post_test_url = self.post_url.text().strip()

    def _load_form(self):
        self.event_name.setText(self.program.event_name)
        self.organizer.setText(self.program.organizer)
        self.logo.setText(self.program.logo)
        self.discussion.setValue(self.program.discussion_minutes)
        self.post_url.setText(self.program.post_test_url)
        self._refresh_table()
        self._refresh_interface_table()

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
        create_backup(path)
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

    def _apply_loaded_program(self, program: Program, status_text: str) -> None:
        self.program = program
        self.program_path = ""
        self._load_form()
        self._clear_autosave()
        self.status.setText(status_text)

    def show_template_dialog(self):
        self._sync_program()
        dialog = TemplateDialog(self, self.program)
        if dialog.exec() and dialog.loaded_program is not None:
            self._apply_loaded_program(dialog.loaded_program, tr("Đã tải mẫu chương trình."))

    def show_backup_dialog(self):
        dialog = BackupDialog(self)
        if dialog.exec() and dialog.loaded_program is not None:
            self._apply_loaded_program(dialog.loaded_program, tr("Đã khôi phục bản sao lưu."))

    def export_schedule(self):
        self._sync_program()
        safe_name = re.sub(r'[\\/:*?"<>|]', "_", self.program.event_name).strip()
        default_name = f"lich_trinh_{safe_name}.pdf" if safe_name else "lich_trinh.pdf"
        path, _ = QFileDialog.getSaveFileName(self, tr("Xuất lịch trình (PDF)"), default_name, "PDF (*.pdf)")
        if not path:
            return
        try:
            export_schedule_pdf(self.program, path)
        except ProgramFileError as exc:
            QMessageBox.critical(self, tr("Không thể xuất PDF"), str(exc))
            return
        self.status.setText(tr("Đã xuất lịch trình: {path}").format(path=path))

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

    def show_interface_media_dialog(self):
        self._sync_program()
        InterfaceMediaDialog(self, self.program).exec()
        self._refresh_interface_table()

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

    def _confirm_interrupt_presentation(self) -> bool:
        return self._confirm(
            tr("Báo cáo viên đang trình bày"),
            tr(
                "Bài trình chiếu hiện tại chưa kết thúc. Chuyển sang phần khác sẽ đóng "
                "bài đang chiếu ngay lập tức. Bạn có chắc chắn?"
            ),
        )

    def next_scene(self):
        if not self.scenes or self.scene_index >= len(self.scenes) - 1:
            return
        if self.ppt.is_running():
            if not self._confirm_interrupt_presentation():
                return
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
            if not self._confirm_interrupt_presentation():
                return
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
        if self.scenes:
            mid_presentation = (
                0 <= self.scene_index < len(self.scenes)
                and self.scenes[self.scene_index]["type"] == "powerpoint"
                and self.ppt.is_running()
            )
            question = (
                tr(
                    "Báo cáo viên đang trình bày dở. Kết thúc ngay sẽ đóng bài đang "
                    "chiếu ngay lập tức. Bạn có chắc chắn?"
                )
                if mid_presentation
                else tr("Bạn có chắc muốn kết thúc trình chiếu hiện tại?")
            )
            if not self._confirm(tr("Kết thúc trình chiếu"), question):
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
