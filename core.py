from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
import json


class ProgramFileError(RuntimeError):
    """Lỗi khi đọc hoặc ghi file chương trình (JSON không hợp lệ, thiếu quyền...)."""


@dataclass
class Report:
    name: str = ""
    department: str = ""
    topic: str = ""
    photo: str = ""
    ppt: str = ""
    duration_minutes: int = 15


#: Các "vai trò" màn hình có thể gán slide/ảnh riêng. "background" là vai trò mặc định —
#: mọi vai trò khác nếu không được gán slide/ảnh riêng sẽ rơi về dùng slide/ảnh của "background".
INTERFACE_ROLES = ["background", "discussion", "post_test", "closing"]


@dataclass
class Program:
    event_name: str = "CHƯƠNG TRÌNH BÁO CÁO"
    organizer: str = ""
    background: str = ""
    logo: str = ""
    discussion_minutes: int = 20
    post_test_url: str = ""
    opening_ppt: str = ""
    closing_ppt: str = ""
    master_ppt: str = ""
    background_slide: int = 0
    discussion_slide: int = 0
    post_test_slide: int = 0
    closing_slide: int = 0
    discussion_image: str = ""
    post_test_image: str = ""
    closing_image: str = ""
    reports: list[Report] = field(default_factory=list)

    def slide_for(self, role: str) -> int:
        return getattr(self, f"{role}_slide", 0)

    def image_override_for(self, role: str) -> str:
        if role == "background":
            return self.background
        return getattr(self, f"{role}_image", "")

    def slide_config_for(self, role: str) -> tuple[str, int]:
        """Trả về (đường_dẫn_file_pptx, số_thứ_tự_slide) nếu vai trò này được gán slide
        từ file chương trình tổng (master_ppt); nếu không thì trả về ("", 0)."""
        slide_number = self.slide_for(role)
        if self.master_ppt and slide_number > 0:
            return self.master_ppt, slide_number
        return "", 0

    @classmethod
    def load(cls, path: str) -> "Program":
        try:
            raw = Path(path).read_text(encoding="utf-8")
        except OSError as exc:
            raise ProgramFileError(f"Không thể đọc file: {exc}") from exc
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ProgramFileError(f"File không đúng định dạng JSON ({exc}).") from exc
        if not isinstance(data, dict):
            raise ProgramFileError("Nội dung file không đúng định dạng chương trình.")
        try:
            reports = [Report(**item) for item in data.pop("reports", [])]
            return cls(**data, reports=reports)
        except TypeError as exc:
            raise ProgramFileError(f"File chứa trường dữ liệu không hợp lệ ({exc}).") from exc

    def save(self, path: str) -> None:
        try:
            Path(path).write_text(
                json.dumps(asdict(self), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError as exc:
            raise ProgramFileError(f"Không thể lưu file: {exc}") from exc

    def _interface_scene(self, ppt_path: str, kind: str) -> dict:
        return {
            "type": "powerpoint",
            "report": Report(name=self.event_name, ppt=ppt_path, duration_minutes=0),
            "interface_kind": kind,
        }

    def scenes(self) -> list[dict]:
        if self.opening_ppt:
            result = [self._interface_scene(self.opening_ppt, "opening")]
        else:
            result = [{"type": "opening", "title": "CHÀO MỪNG QUÝ ĐẠI BIỂU"}]
        for index, report in enumerate(self.reports, start=1):
            result.extend(
                [
                    {"type": "speaker", "report": report, "number": index},
                    {"type": "powerpoint", "report": report, "number": index},
                    {
                        "type": "transition",
                        "title": "TRÂN TRỌNG CẢM ƠN BÁO CÁO VIÊN",
                        "report": report,
                    },
                ]
            )
        result.extend(
            [
                {
                    "type": "discussion",
                    "title": "THẢO LUẬN – HỎI ĐÁP",
                    "duration_minutes": self.discussion_minutes,
                },
                {
                    "type": "post_test",
                    "title": "BÀI KIỂM TRA SAU CHƯƠNG TRÌNH",
                    "url": self.post_test_url,
                },
            ]
        )
        if self.closing_ppt:
            result.append(self._interface_scene(self.closing_ppt, "closing"))
        else:
            result.append({"type": "closing", "title": "TRÂN TRỌNG CẢM ƠN"})
        return result


def validate_program(program: Program) -> list[str]:
    errors: list[str] = []
    if not program.event_name.strip():
        errors.append("Chưa nhập tên chương trình.")
    if program.background and not Path(program.background).is_file():
        errors.append(f"Không tìm thấy ảnh nền: {program.background}")
    if program.logo and not Path(program.logo).is_file():
        errors.append(f"Không tìm thấy ảnh logo: {program.logo}")
    if program.opening_ppt and not Path(program.opening_ppt).is_file():
        errors.append(f"Không tìm thấy file PowerPoint khai mạc: {program.opening_ppt}")
    if program.closing_ppt and not Path(program.closing_ppt).is_file():
        errors.append(f"Không tìm thấy file PowerPoint kết thúc: {program.closing_ppt}")
    any_slide_used = any(program.slide_for(role) > 0 for role in INTERFACE_ROLES)
    if any_slide_used:
        if not program.master_ppt:
            errors.append("Đã chọn slide cho một phần nhưng chưa chọn file chương trình tổng.")
        elif not Path(program.master_ppt).is_file():
            errors.append(f"Không tìm thấy file chương trình tổng: {program.master_ppt}")
    role_labels = {"discussion": "Thảo luận", "post_test": "Post-test", "closing": "Kết thúc"}
    for role, label in role_labels.items():
        image = program.image_override_for(role)
        if image and not Path(image).is_file():
            errors.append(f"Không tìm thấy ảnh riêng cho phần {label}: {image}")
    if not program.reports:
        errors.append("Chưa có báo cáo viên.")
    for index, report in enumerate(program.reports, start=1):
        if not report.name.strip():
            errors.append(f"Báo cáo {index}: thiếu tên báo cáo viên.")
        if not report.topic.strip():
            errors.append(f"Báo cáo {index}: thiếu tên chuyên đề.")
        if not report.ppt:
            errors.append(f"Báo cáo {index}: chưa chọn file PowerPoint.")
        elif not Path(report.ppt).is_file():
            errors.append(f"Báo cáo {index}: không tìm thấy {report.ppt}")
        if report.photo and not Path(report.photo).is_file():
            errors.append(f"Báo cáo {index}: không tìm thấy ảnh {report.photo}")
    return errors

