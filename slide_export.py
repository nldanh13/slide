from __future__ import annotations

from pathlib import Path

from core import Program, Report
from paths import app_dir

CACHE_DIR = app_dir() / "slide_cache"

# Vai trò của scene (StageWindow) -> vai trò cấu hình slide/ảnh trong Program.
# Các loại scene không có mặt ở đây (opening/speaker/transition) luôn dùng vai trò "background".
ROLE_BY_SCENE_TYPE = {
    "discussion": "discussion",
    "post_test": "post_test",
    "closing": "closing",
}


class SlideExportError(RuntimeError):
    """Lỗi khi xuất 1 slide trong file PowerPoint ra ảnh (thiếu PowerPoint, sai số slide...)."""


def _cache_path(ppt_path: Path, slide_number: int) -> Path:
    stat = ppt_path.stat()
    return CACHE_DIR / f"{ppt_path.stem}__{stat.st_mtime_ns}__{slide_number}.png"


def _prune_stale_cache(ppt_path: Path, slide_number: int, keep: Path) -> None:
    pattern = f"{ppt_path.stem}__*__{slide_number}.png"
    for old in CACHE_DIR.glob(pattern):
        if old != keep:
            old.unlink(missing_ok=True)


def export_slide_image(ppt_path: str, slide_number: int) -> str:
    """Xuất 1 slide trong file PowerPoint ra ảnh PNG (có cache theo mtime của file gốc),
    trả về đường dẫn ảnh đã xuất. Chỉ hoạt động trên Windows có cài Microsoft PowerPoint."""
    path = Path(ppt_path)
    if not path.is_file():
        raise SlideExportError(f"Không tìm thấy file: {ppt_path}")

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cached = _cache_path(path, slide_number)
    if cached.is_file():
        return str(cached)

    try:
        import pythoncom
        import win32com.client

        pythoncom.CoInitialize()
        app = win32com.client.DispatchEx("PowerPoint.Application")
        try:
            presentation = app.Presentations.Open(
                str(path.resolve()), ReadOnly=True, WithWindow=False
            )
            try:
                slide_count = presentation.Slides.Count
                if slide_number < 1 or slide_number > slide_count:
                    raise SlideExportError(
                        f"File '{path.name}' chỉ có {slide_count} slide, không có slide {slide_number}."
                    )
                presentation.Slides(slide_number).Export(str(cached), "PNG")
            finally:
                presentation.Close()
        finally:
            app.Quit()
    except SlideExportError:
        raise
    except Exception as exc:
        raise SlideExportError(
            "Không thể xuất ảnh từ slide. Hãy kiểm tra Microsoft PowerPoint đã được cài đặt "
            "và file không bị khóa bởi ứng dụng khác."
        ) from exc

    _prune_stale_cache(path, slide_number, cached)
    return str(cached)


def resolve_scene_image(program: Program, scene_type: str, export=export_slide_image) -> str:
    """Xác định đường dẫn ảnh nền dùng cho 1 loại scene: ưu tiên slide được gán trong file
    chương trình tổng, kế đến ảnh riêng cho vai trò đó, cuối cùng rơi về ảnh nền mặc định.
    Tham số `export` chỉ dùng để dễ kiểm thử (thay bằng hàm giả lập không cần PowerPoint)."""
    role = ROLE_BY_SCENE_TYPE.get(scene_type)
    if role:
        ppt_path, slide_number = program.slide_config_for(role)
        if ppt_path:
            try:
                return export(ppt_path, slide_number)
            except SlideExportError:
                pass
        override = program.image_override_for(role)
        if override:
            return override

    ppt_path, slide_number = program.slide_config_for("background")
    if ppt_path:
        try:
            return export(ppt_path, slide_number)
        except SlideExportError:
            pass
    return program.background


def resolve_report_photo(program: Program, report: Report, export=export_slide_image) -> str:
    """Xác định ảnh đại diện dùng cho báo cáo viên: ưu tiên slide được gán trong file
    chương trình tổng (report.photo_slide), nếu không thì dùng ảnh riêng (report.photo)."""
    if program.master_ppt and report.photo_slide > 0:
        try:
            return export(program.master_ppt, report.photo_slide)
        except SlideExportError:
            pass
    return report.photo
