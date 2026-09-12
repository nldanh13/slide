from __future__ import annotations

from pathlib import Path

# Logic nhận diện file dùng cho luồng nhập nhanh trong MainWindow.import_files():
# chọn file PowerPoint hoặc ảnh, đoán vai trò theo tên file, áp dụng ngay vào
# chương trình — không qua dialog xem trước riêng, việc "setup" (sửa lại vai trò/
# chi tiết nếu đoán sai) diễn ra trực tiếp ở bảng báo cáo viên và bảng giao diện
# chương trình trong cửa sổ chính.

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp"}

# Từ khóa (không dấu, chữ thường) cho biết file PowerPoint là giao diện chương trình
# chứ không phải bài báo cáo của một báo cáo viên cụ thể.
_INTERFACE_KEYWORDS = [
    "khai mac", "chuong trinh", "ket thuc", "mo dau", "giao dien",
    "background", "backgroud", "nen chuong trinh", "trailer",
    "opening", "closing", "intro", "outro", " mc ", "mc_", "mc-",
]
_CLOSING_KEYWORDS = ["ket thuc", "closing", "outro", "cam on", "be mac"]

# Từ khóa nhận diện vai trò của 1 file ẢNH (không phải PowerPoint).
_IMAGE_ROLE_KEYWORDS = {
    "closing_image": ["ket thuc", "closing", "outro", "cam on", "be mac"],
    "post_test": ["post test", "posttest", "kiem tra", "khao sat"],
    "discussion": ["thao luan", "discussion", "hoi dap"],
}


def _strip_diacritics(text: str) -> str:
    import unicodedata

    normalized = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


def _normalized_stem(path: str) -> str:
    stem = _strip_diacritics(Path(path).stem).lower()
    normalized = stem.replace("_", " ").replace("-", " ").replace(".", " ")
    return f" {normalized} "


def guess_report_name(path: str) -> str:
    stem = Path(path).stem
    words = stem.replace("_", " ").replace("-", " ").replace(".", " ").split()
    return " ".join(word.capitalize() for word in words) if words else stem


def classify_ppt_filename(path: str) -> str:
    """Đoán vai trò của 1 file PowerPoint dựa theo tên: 'opening', 'closing' hoặc 'speaker'."""
    padded = _normalized_stem(path)
    if any(keyword in padded for keyword in _INTERFACE_KEYWORDS):
        if any(keyword in padded for keyword in _CLOSING_KEYWORDS):
            return "closing"
        return "opening"
    return "speaker"


def classify_image_filename(path: str) -> str:
    """Đoán vai trò của 1 file ảnh: 'discussion', 'post_test', 'closing_image',
    mặc định 'background' nếu không đoán được từ khóa nào."""
    padded = _normalized_stem(path)
    for role, keywords in _IMAGE_ROLE_KEYWORDS.items():
        if any(keyword in padded for keyword in keywords):
            return role
    return "background"


def classify_file(path: str) -> str:
    """Đoán vai trò cho 1 file bất kỳ (PowerPoint hoặc ảnh) khi nhập nhanh:
    'speaker' | 'opening' | 'closing' (PowerPoint), hoặc
    'background' | 'discussion' | 'post_test' | 'closing_image' (ảnh)."""
    if Path(path).suffix.lower() in IMAGE_EXTENSIONS:
        return classify_image_filename(path)
    return classify_ppt_filename(path)
