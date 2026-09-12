import shutil
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

import backups
from core import Program, ProgramFileError


class BackupsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        dir_patcher = mock.patch.object(backups, "BACKUPS_DIR", Path(self.tmp) / "backups")
        dir_patcher.start()
        self.addCleanup(dir_patcher.stop)
        max_patcher = mock.patch.object(backups, "MAX_BACKUPS_PER_FILE", 3)
        max_patcher.start()
        self.addCleanup(max_patcher.stop)

        self.src = Path(self.tmp) / "chuong_trinh.json"

    def _save_version(self, name: str) -> None:
        Program(event_name=name).save(str(self.src))
        backups.create_backup(str(self.src))

    def test_no_backup_when_source_missing(self):
        self.assertIsNone(backups.create_backup(str(self.src)))

    def test_creates_one_backup_per_save(self):
        self._save_version("V1")
        self.assertEqual(len(backups.list_backups()), 1)

    def test_prunes_to_max_backups_keeping_newest(self):
        for i in range(5):
            self._save_version(f"V{i}")
            time.sleep(1.01)  # đảm bảo timestamp (giây) khác nhau giữa các lần lưu

        kept = backups.list_backups()
        self.assertEqual(len(kept), 3, "phải giữ đúng số lượng bản sao lưu tối đa cho phép")
        newest = Program.load(str(kept[0]))
        self.assertEqual(newest.event_name, "V4")

    def test_does_not_prune_when_under_the_limit(self):
        # Đây là hồi quy cho lỗi excess âm bị Python hiểu là list[:-n] thay vì rỗng.
        for i in range(2):
            self._save_version(f"V{i}")
            time.sleep(1.01)
        self.assertEqual(len(backups.list_backups()), 2)

    def test_backup_display_name_formats_timestamp(self):
        self._save_version("V1")
        name = backups.backup_display_name(backups.list_backups()[0])
        self.assertIn("chuong_trinh", name)
        self.assertIn("—", name)

    def test_backup_can_be_loaded_back(self):
        self._save_version("Phiên bản gốc")
        loaded = Program.load(str(backups.list_backups()[0]))
        self.assertEqual(loaded.event_name, "Phiên bản gốc")

    def test_loading_nonexistent_backup_raises(self):
        with self.assertRaises(ProgramFileError):
            Program.load(str(backups.BACKUPS_DIR / "khong_ton_tai.json"))


if __name__ == "__main__":
    unittest.main()
