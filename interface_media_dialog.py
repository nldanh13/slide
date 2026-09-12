from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from core import Program
from file_library import pick_file
from i18n import tr

_ROLE_LABELS = {
    "discussion": "Thảo luận",
    "post_test": "Post-test",
    "closing": "Kết thúc",
}


class InterfaceMediaDialog(QDialog):
    """Cấu hình slide (từ 1 file chương trình tổng) hoặc ảnh riêng cho từng phần:
    Nền/mặc định, Thảo luận, Post-test, Kết thúc. Chỉnh trên bản nháp, chỉ áp dụng
    vào chương trình thật khi bấm Lưu."""

    def __init__(self, parent, program: Program):
        super().__init__(parent)
        self.program = program
        self.setWindowTitle(tr("Slide / ảnh riêng cho từng phần"))
        self.setMinimumWidth(560)

        info = QLabel(tr(
            "Chọn 1 file PowerPoint \"chương trình tổng\" rồi gán số thứ tự slide tương ứng "
            "cho từng phần bên dưới — ứng dụng sẽ tự xuất slide đó thành ảnh nền (cần cài "
            "Microsoft PowerPoint). Để trống (0) nghĩa là không dùng slide cho phần đó; khi "
            "đó ứng dụng dùng ảnh riêng (nếu có) hoặc ảnh nền mặc định."
        ))
        info.setWordWrap(True)

        master_row = QHBoxLayout()
        self.master_ppt_edit = QLineEdit(self.program.master_ppt)
        self.master_ppt_edit.setReadOnly(True)
        self.choose_master_btn = QPushButton(tr("Chọn…"))
        self.choose_master_btn.clicked.connect(self._choose_master_ppt)
        clear_master_btn = QPushButton(tr("Xóa"))
        clear_master_btn.clicked.connect(self._clear_master_ppt)
        master_row.addWidget(self.master_ppt_edit, 1)
        master_row.addWidget(self.choose_master_btn)
        master_row.addWidget(clear_master_btn)

        master_form = QFormLayout()
        master_form.addRow(tr("File chương trình tổng (PowerPoint)"), master_row)

        grid = QGridLayout()
        grid.addWidget(QLabel(f"<b>{tr('Phần')}</b>"), 0, 0)
        grid.addWidget(QLabel(f"<b>{tr('Số slide')}</b>"), 0, 1)
        grid.addWidget(QLabel(f"<b>{tr('Ảnh riêng (nếu không dùng slide)')}</b>"), 0, 2)

        self.slide_spins: dict[str, QSpinBox] = {}
        self.image_edits: dict[str, QLineEdit] = {}
        self.image_choose_buttons: dict[str, QPushButton] = {}

        grid.addWidget(QLabel(tr("Nền / Mở đầu (mặc định)")), 1, 0)
        bg_spin = QSpinBox()
        bg_spin.setRange(0, 999)
        bg_spin.setValue(self.program.background_slide)
        bg_spin.setSpecialValueText(tr("Không dùng"))
        self.slide_spins["background"] = bg_spin
        grid.addWidget(bg_spin, 1, 1)
        grid.addWidget(QLabel(tr("(dùng ô \"Background\" ở màn hình chính)")), 1, 2)

        row = 2
        for role, label in _ROLE_LABELS.items():
            grid.addWidget(QLabel(tr(label)), row, 0)
            spin = QSpinBox()
            spin.setRange(0, 999)
            spin.setValue(self.program.slide_for(role))
            spin.setSpecialValueText(tr("Không dùng"))
            self.slide_spins[role] = spin
            grid.addWidget(spin, row, 1)

            image_box = QWidget()
            image_row = QHBoxLayout(image_box)
            image_row.setContentsMargins(0, 0, 0, 0)
            edit = QLineEdit(self.program.image_override_for(role))
            edit.setReadOnly(True)
            self.image_edits[role] = edit
            choose_btn = QPushButton(tr("Chọn…"))
            choose_btn.clicked.connect(lambda _checked=False, r=role: self._choose_image(r))
            self.image_choose_buttons[role] = choose_btn
            clear_btn = QPushButton(tr("Xóa"))
            clear_btn.clicked.connect(lambda _checked=False, r=role: self.image_edits[r].clear())
            image_row.addWidget(edit, 1)
            image_row.addWidget(choose_btn)
            image_row.addWidget(clear_btn)
            grid.addWidget(image_box, row, 2)
            row += 1

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText(tr("Lưu"))
        buttons.button(QDialogButtonBox.Cancel).setText(tr("Hủy"))
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(info)
        layout.addLayout(master_form)
        layout.addLayout(grid)
        layout.addStretch()
        layout.addWidget(buttons)

    def _choose_master_ppt(self):
        path = pick_file(self, self.program, self.choose_master_btn, "ppt")
        if path:
            self.master_ppt_edit.setText(path)

    def _clear_master_ppt(self):
        self.master_ppt_edit.clear()

    def _choose_image(self, role: str):
        path = pick_file(self, self.program, self.image_choose_buttons[role], "image")
        if path:
            self.image_edits[role].setText(path)

    def _accept(self):
        self.program.master_ppt = self.master_ppt_edit.text().strip()
        self.program.background_slide = self.slide_spins["background"].value()
        for role in _ROLE_LABELS:
            setattr(self.program, f"{role}_slide", self.slide_spins[role].value())
            setattr(self.program, f"{role}_image", self.image_edits[role].text().strip())
        self.accept()
