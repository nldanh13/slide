from __future__ import annotations

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from core import Program, ProgramFileError
from i18n import tr
import backups


class BackupDialog(QDialog):
    """Xem và khôi phục các bản sao lưu được tạo tự động mỗi lần Lưu chương trình."""

    def __init__(self, parent):
        super().__init__(parent)
        self.loaded_program: Program | None = None
        self.setWindowTitle(tr("Khôi phục bản sao lưu"))
        self.setMinimumWidth(420)

        info = QLabel(tr(
            "Mỗi lần bấm Lưu chương trình, ứng dụng tự giữ thêm một bản sao lưu có "
            "ngày giờ. Chọn một bản bên dưới để khôi phục nếu chỉnh sửa nhầm."
        ))
        info.setWordWrap(True)

        self.list_widget = QListWidget()
        self._backup_paths = backups.list_backups()
        self.list_widget.addItems([backups.backup_display_name(p) for p in self._backup_paths])

        restore_btn = QPushButton(tr("Khôi phục bản đã chọn"))
        restore_btn.clicked.connect(self._restore_selected)
        open_folder_btn = QPushButton(tr("Mở thư mục sao lưu"))
        open_folder_btn.clicked.connect(self._open_folder)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.button(QDialogButtonBox.Close).setText(tr("Đóng"))
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(info)
        layout.addWidget(self.list_widget, 1)
        layout.addWidget(restore_btn)
        layout.addWidget(open_folder_btn)
        layout.addWidget(buttons)

    def _restore_selected(self):
        row = self.list_widget.currentRow()
        if row < 0:
            return
        path = self._backup_paths[row]
        try:
            self.loaded_program = Program.load(str(path))
        except ProgramFileError as exc:
            QMessageBox.critical(self, tr("Không thể khôi phục"), str(exc))
            return
        self.accept()

    def _open_folder(self):
        backups.BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(backups.BACKUPS_DIR)))
