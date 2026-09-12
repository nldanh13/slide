from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from core import Program, Report
from i18n import tr

# Từ khóa (không dấu, chữ thường) cho biết file là giao diện chương trình chứ không phải
# bài báo cáo của một báo cáo viên cụ thể.
_INTERFACE_KEYWORDS = [
    "khai mac", "chuong trinh", "ket thuc", "mo dau", "giao dien",
    "background", "backgroud", "nen chuong trinh", "trailer",
    "opening", "closing", "intro", "outro", " mc ", "mc_", "mc-",
]
_CLOSING_KEYWORDS = ["ket thuc", "closing", "outro", "cam on", "be mac"]

CLASSIFICATIONS = ["speaker", "opening", "closing", "skip"]


def _strip_diacritics(text: str) -> str:
    import unicodedata

    normalized = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


def guess_report_name(path: str) -> str:
    stem = Path(path).stem
    words = stem.replace("_", " ").replace("-", " ").replace(".", " ").split()
    return " ".join(word.capitalize() for word in words) if words else stem


def classify_ppt_filename(path: str) -> str:
    """Đoán loại file dựa theo tên: 'opening', 'closing' hoặc 'speaker'."""
    stem = _strip_diacritics(Path(path).stem).lower()
    normalized = stem.replace("_", " ").replace("-", " ").replace(".", " ")
    padded = f" {normalized} "
    if any(keyword in padded for keyword in _INTERFACE_KEYWORDS):
        if any(keyword in padded for keyword in _CLOSING_KEYWORDS):
            return "closing"
        return "opening"
    return "speaker"


class BulkImportDialog(QDialog):
    """Cho phép chọn nhiều file PowerPoint cùng lúc; ứng dụng gợi ý phân loại
    (báo cáo viên / giao diện mở đầu / giao diện kết thúc) và người dùng xác nhận
    lại trước khi áp dụng vào chương trình."""

    LABELS = {
        "speaker": "Báo cáo viên",
        "opening": "Giao diện – Mở đầu",
        "closing": "Giao diện – Kết thúc",
        "skip": "Bỏ qua",
    }

    def __init__(self, parent, program: Program):
        super().__init__(parent)
        self.program = program
        self.setWindowTitle(tr("Nhập nhiều file PowerPoint"))
        self.setMinimumWidth(720)

        info = QLabel(tr(
            "Chọn nhiều file PowerPoint cùng lúc. Ứng dụng sẽ đoán file nào là bài báo cáo "
            "và file nào là giao diện mở đầu/kết thúc dựa theo tên file — hãy kiểm tra và "
            "sửa lại phân loại nếu đoán sai trước khi bấm Nhập."
        ))
        info.setWordWrap(True)

        choose_btn = QPushButton(tr("Chọn file PowerPoint…"))
        choose_btn.clicked.connect(self._choose_files)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels([tr("File"), tr("Tên báo cáo viên (tạm)"), tr("Phân loại")])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText(tr("Nhập"))
        buttons.button(QDialogButtonBox.Cancel).setText(tr("Hủy"))
        buttons.accepted.connect(self._apply)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(info)
        layout.addWidget(choose_btn)
        layout.addWidget(self.table, 1)
        layout.addWidget(buttons)

    def _choose_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, tr("Chọn file PowerPoint"), "",
            "PowerPoint (*.ppt *.pptx *.pptm *.pps *.ppsx)",
        )
        if not paths:
            return
        self.table.setRowCount(len(paths))
        for row, path in enumerate(paths):
            file_item = QTableWidgetItem(Path(path).name)
            file_item.setData(Qt.UserRole, path)
            self.table.setItem(row, 0, file_item)
            self.table.setItem(row, 1, QTableWidgetItem(guess_report_name(path)))
            combo = QComboBox()
            for key in CLASSIFICATIONS:
                combo.addItem(tr(self.LABELS[key]), key)
            guessed = classify_ppt_filename(path)
            combo.setCurrentIndex(combo.findData(guessed))
            self.table.setCellWidget(row, 2, combo)

    def _apply(self):
        added_reports = 0
        for row in range(self.table.rowCount()):
            file_item = self.table.item(row, 0)
            path = file_item.data(Qt.UserRole)
            classification = self.table.cellWidget(row, 2).currentData()
            if classification == "speaker":
                name = self.table.item(row, 1).text().strip() or guess_report_name(path)
                self.program.reports.append(Report(name=name, ppt=path))
                added_reports += 1
            elif classification == "opening":
                self.program.opening_ppt = path
            elif classification == "closing":
                self.program.closing_ppt = path
        self._imported_count = added_reports
        self.accept()
