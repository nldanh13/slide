from __future__ import annotations

import re

from core import Program, ProgramFileError
from paths import app_dir

TEMPLATES_DIR = app_dir() / "templates"
_SAFE_CHARS = re.compile(r"[^\w\- ]", re.UNICODE)


class TemplateNameError(ValueError):
    """Tên mẫu chương trình không hợp lệ (rỗng hoặc chỉ chứa ký tự không cho phép)."""


def _sanitize_name(name: str) -> str:
    cleaned = _SAFE_CHARS.sub("", name).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    if not cleaned:
        raise TemplateNameError("Tên mẫu không được để trống hoặc chỉ chứa ký tự đặc biệt.")
    return cleaned[:80]


def _template_path(name: str):
    return TEMPLATES_DIR / f"{_sanitize_name(name)}.json"


def list_templates() -> list[str]:
    if not TEMPLATES_DIR.is_dir():
        return []
    return sorted(path.stem for path in TEMPLATES_DIR.glob("*.json"))


def save_template(name: str, program: Program) -> None:
    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    program.save(str(_template_path(name)))


def load_template(name: str) -> Program:
    return Program.load(str(_template_path(name)))


def delete_template(name: str) -> None:
    path = _template_path(name)
    try:
        path.unlink(missing_ok=True)
    except OSError as exc:
        raise ProgramFileError(f"Không thể xóa mẫu: {exc}") from exc


def template_exists(name: str) -> bool:
    return _template_path(name).is_file()
