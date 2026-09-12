from __future__ import annotations

import sys

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from i18n import LANGUAGES, get_language, set_language, tr
from paths import app_dir
from remote import RemoteControl, local_ip
from settings import APP_VERSION, AppSettings

README_PATH = app_dir() / "README.md"


def _powerpoint_library_available() -> bool:
    try:
        import win32com.client  # noqa: F401
    except ImportError:
        return False
    return True


class SettingsDialog(QDialog):
    def __init__(self, parent, settings: AppSettings, remote: RemoteControl, screen_combo: QComboBox):
        super().__init__(parent)
        self.settings = settings
        self.remote = remote
        self.screen_combo = screen_combo
        self.setWindowTitle(tr("Cài đặt"))
        self.setMinimumWidth(480)

        tabs = QTabWidget()
        tabs.addTab(self._build_language_tab(), tr("Ngôn ngữ"))
        tabs.addTab(self._build_machine_tab(), tr("Cấu hình máy"))
        tabs.addTab(self._build_support_tab(), tr("Hỗ trợ"))

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.button(QDialogButtonBox.Close).setText(tr("Đóng cửa sổ này"))
        buttons.rejected.connect(self.accept)
        buttons.accepted.connect(self.accept)

        layout = QVBoxLayout(self)
        layout.addWidget(tabs)
        layout.addWidget(buttons)

    # ---- Tab: Ngôn ngữ ----
    def _build_language_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        description = QLabel(tr(
            "Chọn ngôn ngữ hiển thị cho cửa sổ điều khiển. Màn hình sân khấu vẫn hiển thị "
            "đúng theo nội dung chương trình (tên chương trình, tên báo cáo viên...) mà bạn nhập, "
            "không phụ thuộc vào ngôn ngữ giao diện."
        ))
        description.setWordWrap(True)

        form = QFormLayout()
        self.language_combo = QComboBox()
        for code, label in LANGUAGES.items():
            self.language_combo.addItem(label, code)
        current_index = self.language_combo.findData(get_language())
        if current_index >= 0:
            self.language_combo.setCurrentIndex(current_index)
        self.language_combo.currentIndexChanged.connect(self._on_language_changed)
        form.addRow(tr("Ngôn ngữ giao diện"), self.language_combo)

        note = QLabel(tr(
            "Áp dụng ngay lập tức. Nhãn có sẵn trên màn hình có thể cần mở lại cửa sổ để cập nhật hết."
        ))
        note.setWordWrap(True)
        note.setStyleSheet("color: #64748b; font-size: 9pt;")

        layout.addWidget(description)
        layout.addLayout(form)
        layout.addWidget(note)
        layout.addStretch()
        return widget

    def _on_language_changed(self):
        code = self.language_combo.currentData()
        set_language(code)
        self.settings.language = code
        self.settings.save()
        main_window = self.parent()
        if main_window is not None and hasattr(main_window, "retranslate_visible_texts"):
            main_window.retranslate_visible_texts()
        self.setWindowTitle(tr("Cài đặt"))

    # ---- Tab: Cấu hình máy ----
    def _build_machine_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        form = QFormLayout()

        self.port_spin = QSpinBox()
        self.port_spin.setRange(1024, 65535)
        self.port_spin.setValue(self.settings.remote_port)
        self.port_spin.editingFinished.connect(self._apply_port_change)
        form.addRow(tr("Cổng máy chủ điều khiển từ xa"), self.port_spin)

        port_note = QLabel(tr(
            "Đổi cổng sẽ khởi động lại máy chủ điều khiển từ xa ngay lập tức "
            "(mọi mã QR/đường dẫn cũ sẽ không dùng được nữa)."
        ))
        port_note.setWordWrap(True)
        port_note.setStyleSheet("color: #64748b; font-size: 9pt;")

        self.default_screen_combo = QComboBox()
        self.default_screen_combo.addItem(tr("Tự động (ưu tiên màn hình phụ)"), -1)
        for index in range(self.screen_combo.count()):
            self.default_screen_combo.addItem(self.screen_combo.itemText(index), index)
        saved_index = self.default_screen_combo.findData(self.settings.preferred_screen_index)
        self.default_screen_combo.setCurrentIndex(saved_index if saved_index >= 0 else 0)
        self.default_screen_combo.currentIndexChanged.connect(self._apply_default_screen)
        form.addRow(tr("Màn hình sân khấu mặc định"), self.default_screen_combo)

        layout.addLayout(form)
        layout.addWidget(port_note)

        layout.addWidget(QLabel(f"<b>{tr('Kiểm tra hệ thống')}</b>"))
        self.system_check_label = QLabel()
        self.system_check_label.setWordWrap(True)
        self._refresh_system_check()
        recheck_btn = QPushButton(tr("Kiểm tra lại"))
        recheck_btn.clicked.connect(self._refresh_system_check)
        layout.addWidget(self.system_check_label)
        layout.addWidget(recheck_btn)
        layout.addStretch()
        return widget

    def _apply_port_change(self):
        port = self.port_spin.value()
        if port == self.settings.remote_port:
            return
        self.settings.remote_port = port
        self.settings.save()
        self.remote.stop()
        self.remote.start(port=port)
        main_window = self.parent()
        if main_window is not None and hasattr(main_window, "refresh_remote_status"):
            main_window.refresh_remote_status()

    def _apply_default_screen(self):
        self.settings.preferred_screen_index = self.default_screen_combo.currentData()
        self.settings.save()

    def _refresh_system_check(self):
        screens = QApplication.screens()
        ppt_ok = _powerpoint_library_available()
        lines = [
            f"{tr('Số màn hình phát hiện')}: {len(screens)}",
            f"{tr('Điều khiển PowerPoint (COM)')}: "
            + (tr("Có sẵn") if ppt_ok else tr("Không khả dụng (chỉ chạy được trên Windows có PowerPoint)")),
            f"{tr('Địa chỉ IP mạng nội bộ')}: {local_ip()}",
            f"{tr('Phiên bản Python')}: {sys.version.split()[0]}",
        ]
        self.system_check_label.setText("<br>".join(lines))

    # ---- Tab: Hỗ trợ ----
    def _build_support_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        layout.addWidget(QLabel(f"<b>{tr('Phím tắt')}</b>"))
        shortcuts = QLabel(
            "<br>".join(
                tr(text)
                for text in [
                    "F5: bắt đầu chương trình.",
                    "Ctrl + →: chuyển sang phần kế tiếp.",
                    "Ctrl + ←: quay lại phần trước.",
                    "Esc: kết thúc toàn bộ trình chiếu khi cửa sổ điều khiển đang được chọn.",
                ]
            )
        )
        layout.addWidget(shortcuts)

        readme_btn = QPushButton(tr("Mở hướng dẫn sử dụng (README)"))
        readme_btn.clicked.connect(self._open_readme)
        layout.addWidget(readme_btn)

        layout.addWidget(QLabel(f"{tr('Phiên bản ứng dụng')}: {APP_VERSION}"))
        layout.addStretch()
        return widget

    def _open_readme(self):
        if not README_PATH.is_file() or not QDesktopServices.openUrl(QUrl.fromLocalFile(str(README_PATH))):
            QMessageBox.warning(self, tr("Không thể mở file hướng dẫn"), str(README_PATH))
