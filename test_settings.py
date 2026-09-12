import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import settings
from settings import AppSettings


class AppSettingsTest(unittest.TestCase):
    def _with_temp_path(self, folder: str):
        return mock.patch.object(settings, "SETTINGS_PATH", Path(folder) / "app_settings.json")

    def test_load_returns_defaults_when_file_missing(self):
        with tempfile.TemporaryDirectory() as folder, self._with_temp_path(folder):
            loaded = AppSettings.load()
        self.assertEqual(loaded, AppSettings())

    def test_save_and_load_round_trip(self):
        with tempfile.TemporaryDirectory() as folder, self._with_temp_path(folder):
            original = AppSettings(language="en", remote_port=9000, preferred_screen_index=1)
            original.save()
            loaded = AppSettings.load()
        self.assertEqual(loaded, original)

    def test_load_ignores_unknown_fields(self):
        with tempfile.TemporaryDirectory() as folder, self._with_temp_path(folder):
            path = Path(folder) / "app_settings.json"
            path.write_text(
                json.dumps({"language": "en", "truong_la": "khong biet"}), encoding="utf-8"
            )
            loaded = AppSettings.load()
        self.assertEqual(loaded.language, "en")

    def test_load_returns_defaults_on_malformed_json(self):
        with tempfile.TemporaryDirectory() as folder, self._with_temp_path(folder):
            path = Path(folder) / "app_settings.json"
            path.write_text("{khong phai json", encoding="utf-8")
            loaded = AppSettings.load()
        self.assertEqual(loaded, AppSettings())


if __name__ == "__main__":
    unittest.main()
