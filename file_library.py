from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QFileDialog, QMenu, QPushButton

from core import Program
from i18n import tr

PPT_FILTER = "PowerPoint (*.ppt *.pptx *.pptm *.pps *.ppsx)"
IMAGE_FILTER = "Ảnh (*.png *.jpg *.jpeg *.bmp)"


def choose_file(parent, title: str, file_filter: str) -> str:
    """Mở hộp thoại duyệt file bình thường của hệ điều hành, không qua thư viện."""
    value, _ = QFileDialog.getOpenFileName(parent, title, "", file_filter)
    return value


def pick_file(parent, program: Program, anchor_button: QPushButton, kind: str) -> str:
    """Chọn 1 file PowerPoint/ảnh: ưu tiên cho chọn lại file đã nhập trước đó ở bất kỳ
    đâu trong chương trình (thư viện dùng chung — mỗi file chỉ cần duyệt 1 lần), hoặc
    nhập file mới từ máy nếu chưa có trong thư viện. Thay cho việc mỗi nơi trong ứng
    dụng tự mở hộp thoại duyệt file riêng lẻ, rối và không liên kết với nhau.
    Trả về đường dẫn đã chọn, hoặc "" nếu người dùng hủy."""
    library = program.ppt_library if kind == "ppt" else program.image_library
    file_filter = PPT_FILTER if kind == "ppt" else IMAGE_FILTER

    if not library:
        # Chưa có file nào trong thư viện để chọn lại — mở thẳng hộp thoại duyệt file,
        # khỏi hiện menu chỉ có mỗi lựa chọn "Nhập file mới…".
        new_path = choose_file(parent, tr("Chọn file"), file_filter)
        if new_path:
            program.remember_file(new_path)
        return new_path

    menu = QMenu(anchor_button)
    for path in library:
        action = menu.addAction(Path(path).name)
        action.setToolTip(path)
        action.setData(path)
    menu.addSeparator()
    import_action = menu.addAction(tr("📁 Nhập file mới…"))
    import_action.setData(None)

    chosen = menu.exec(anchor_button.mapToGlobal(anchor_button.rect().bottomLeft()))
    if chosen is None:
        return ""
    path = chosen.data()
    if path is not None:
        return path

    new_path = choose_file(parent, tr("Chọn file"), file_filter)
    if new_path:
        program.remember_file(new_path)
    return new_path
