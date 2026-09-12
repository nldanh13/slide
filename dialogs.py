from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from core import Report
from i18n import tr
from qr_utils import make_qr_pixmap
from remote import RemoteControl


def choose_file(parent, title, file_filter):
    value, _ = QFileDialog.getOpenFileName(parent, title, "", file_filter)
    return value


class ReportDialog(QDialog):
    def __init__(self, parent=None, report: Report | None = None):
        super().__init__(parent)
        self.setWindowTitle(tr("Thông tin báo cáo viên"))
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
        form.addRow(tr("Họ tên, học hàm/học vị*"), self.name)
        form.addRow(tr("Đơn vị"), self.department)
        form.addRow(tr("Tên chuyên đề*"), self.topic)
        form.addRow(tr("Ảnh báo cáo viên"), self._path_row(self.photo, "Ảnh (*.png *.jpg *.jpeg)"))
        form.addRow(tr("File PowerPoint*"), self._path_row(self.ppt, "PowerPoint (*.ppt *.pptx *.pptm *.pps *.ppsx)"))
        form.addRow(tr("Thời lượng dự kiến (phút)"), self.duration)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText(tr("Lưu"))
        buttons.button(QDialogButtonBox.Cancel).setText(tr("Hủy"))
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def _path_row(self, edit, file_filter):
        box = QWidget()
        row = QHBoxLayout(box)
        row.setContentsMargins(0, 0, 0, 0)
        button = QPushButton(tr("Chọn…"))
        button.clicked.connect(
            lambda: (value := choose_file(self, tr("Chọn file"), file_filter)) and edit.setText(value)
        )
        row.addWidget(edit, 1)
        row.addWidget(button)
        return box

    def _accept(self):
        if not self.name.text().strip() or not self.topic.text().strip() or not self.ppt.text().strip():
            QMessageBox.warning(self, tr("Thiếu thông tin"), tr(
                "Vui lòng nhập họ tên, chuyên đề và chọn file PowerPoint."
            ))
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
        self.setWindowTitle(tr("Điều khiển từ xa"))
        self.setMinimumWidth(360)

        url = remote.url()

        info = QLabel(tr(
            "Dùng điện thoại kết nối cùng Wi-Fi với máy tính này, quét mã QR "
            "hoặc mở đường dẫn bên dưới bằng trình duyệt để điều khiển chương trình."
        ))
        info.setWordWrap(True)

        qr_label = QLabel()
        qr_label.setAlignment(Qt.AlignCenter)
        pixmap = make_qr_pixmap(url, 240)
        if pixmap is not None:
            qr_label.setPixmap(pixmap)
        else:
            qr_label.setText(tr("Không tạo được mã QR"))

        link = QLineEdit(url)
        link.setReadOnly(True)

        note = QLabel(tr(
            "Lưu ý: liên kết chỉ dùng được khi điện thoại và máy tính cùng mạng Wi-Fi. "
            "Khởi động lại ứng dụng sẽ tạo mã truy cập mới."
        ))
        note.setWordWrap(True)
        note.setStyleSheet("color: #9aa3b2; font-size: 9pt;")

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.button(QDialogButtonBox.Close).setText(tr("Đóng"))
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)

        layout = QVBoxLayout(self)
        layout.addWidget(info)
        layout.addWidget(qr_label)
        layout.addWidget(link)
        layout.addWidget(note)
        layout.addWidget(buttons)
