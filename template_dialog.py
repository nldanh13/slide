from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from core import Program, ProgramFileError
from i18n import tr
import templates


class TemplateDialog(QDialog):
    """Lưu chương trình hiện tại làm mẫu, hoặc tải một mẫu đã lưu trước đó."""

    def __init__(self, parent, current_program: Program):
        super().__init__(parent)
        self.current_program = current_program
        self.loaded_program: Program | None = None
        self.setWindowTitle(tr("Mẫu chương trình"))
        self.setMinimumWidth(420)

        info = QLabel(tr(
            "Lưu chương trình hiện tại làm mẫu để dùng lại cho các sự kiện sau, hoặc "
            "chọn một mẫu có sẵn để tải vào chương trình đang chỉnh sửa."
        ))
        info.setWordWrap(True)

        self.list_widget = QListWidget()
        self._refresh_list()

        save_btn = QPushButton(tr("Lưu chương trình hiện tại làm mẫu mới…"))
        save_btn.clicked.connect(self._save_as_template)
        load_btn = QPushButton(tr("Tải mẫu đã chọn"))
        load_btn.clicked.connect(self._load_selected)
        delete_btn = QPushButton(tr("Xóa mẫu đã chọn"))
        delete_btn.clicked.connect(self._delete_selected)

        action_row = QHBoxLayout()
        action_row.addWidget(load_btn)
        action_row.addWidget(delete_btn)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.button(QDialogButtonBox.Close).setText(tr("Đóng"))
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(info)
        layout.addWidget(self.list_widget, 1)
        layout.addLayout(action_row)
        layout.addWidget(save_btn)
        layout.addWidget(buttons)

    def _refresh_list(self):
        self.list_widget.clear()
        self.list_widget.addItems(templates.list_templates())

    def _selected_name(self) -> str | None:
        item = self.list_widget.currentItem()
        return item.text() if item else None

    def _save_as_template(self):
        name, ok = QInputDialog.getText(self, tr("Lưu làm mẫu"), tr("Tên mẫu chương trình:"))
        if not ok or not name.strip():
            return
        if templates.template_exists(name) and QMessageBox.question(
            self, tr("Ghi đè mẫu"), tr("Đã có mẫu cùng tên. Ghi đè?")
        ) != QMessageBox.Yes:
            return
        try:
            templates.save_template(name, self.current_program)
        except (templates.TemplateNameError, ProgramFileError) as exc:
            QMessageBox.critical(self, tr("Không thể lưu mẫu"), str(exc))
            return
        self._refresh_list()

    def _load_selected(self):
        name = self._selected_name()
        if not name:
            return
        if self.current_program.reports and QMessageBox.question(
            self, tr("Tải mẫu"),
            tr("Dữ liệu báo cáo viên hiện tại chưa được lưu sẽ bị thay thế. Tiếp tục?"),
        ) != QMessageBox.Yes:
            return
        try:
            self.loaded_program = templates.load_template(name)
        except (templates.TemplateNameError, ProgramFileError) as exc:
            QMessageBox.critical(self, tr("Không thể tải mẫu"), str(exc))
            return
        self.accept()

    def _delete_selected(self):
        name = self._selected_name()
        if not name:
            return
        if QMessageBox.question(
            self, tr("Xóa mẫu"), tr("Xóa mẫu \"{name}\"?").format(name=name)
        ) != QMessageBox.Yes:
            return
        try:
            templates.delete_template(name)
        except ProgramFileError as exc:
            QMessageBox.critical(self, tr("Không thể xóa mẫu"), str(exc))
            return
        self._refresh_list()
