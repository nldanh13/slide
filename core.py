from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
import json


@dataclass
class Report:
    name: str = ""
    department: str = ""
    topic: str = ""
    photo: str = ""
    ppt: str = ""
    duration_minutes: int = 15


@dataclass
class Program:
    event_name: str = "CHƯƠNG TRÌNH BÁO CÁO"
    organizer: str = ""
    background: str = ""
    logo: str = ""
    discussion_minutes: int = 20
    post_test_url: str = ""
    reports: list[Report] = field(default_factory=list)

    @classmethod
    def load(cls, path: str) -> "Program":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        reports = [Report(**item) for item in data.pop("reports", [])]
        return cls(**data, reports=reports)

    def save(self, path: str) -> None:
        Path(path).write_text(
            json.dumps(asdict(self), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def scenes(self) -> list[dict]:
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
                {"type": "closing", "title": "TRÂN TRỌNG CẢM ƠN"},
            ]
        )
        return result


def validate_program(program: Program) -> list[str]:
    errors: list[str] = []
    if not program.event_name.strip():
        errors.append("Chưa nhập tên chương trình.")
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
    return errors

