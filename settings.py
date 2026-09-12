from __future__ import annotations

import json
import dataclasses
from dataclasses import asdict, dataclass
from pathlib import Path

SETTINGS_PATH = Path(__file__).resolve().parent / "app_settings.json"
APP_VERSION = "1.1.0"


@dataclass
class AppSettings:
    language: str = "vi"
    remote_port: int = 8765
    preferred_screen_index: int = -1  # -1 nghĩa là tự động (ưu tiên màn hình phụ)

    @classmethod
    def load(cls) -> "AppSettings":
        if not SETTINGS_PATH.is_file():
            return cls()
        try:
            data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return cls()
        if not isinstance(data, dict):
            return cls()
        known_fields = {f.name for f in dataclasses.fields(cls)}
        filtered = {key: value for key, value in data.items() if key in known_fields}
        try:
            return cls(**filtered)
        except TypeError:
            return cls()

    def save(self) -> None:
        try:
            SETTINGS_PATH.write_text(
                json.dumps(asdict(self), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError:
            pass
