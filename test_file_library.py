import shutil
import tempfile
import unittest
from pathlib import Path

from PySide6.QtWidgets import QApplication, QFileDialog, QPushButton

from core import Program
from file_library import pick_file


class PickFileTest(unittest.TestCase):
    """pick_file() ưu tiên cho chọn lại file đã có trong thư viện của chương trình
    (tránh mỗi nơi tự mở hộp thoại duyệt file riêng lẻ); chỉ mở hộp thoại duyệt file
    khi thư viện đang trống hoặc người dùng chủ động chọn "Nhập file mới…"."""

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.button = QPushButton()
        self._orig_get_open_file_name = QFileDialog.getOpenFileName
        self.addCleanup(setattr, QFileDialog, "getOpenFileName", self._orig_get_open_file_name)

    def _make_file(self, name: str) -> str:
        path = Path(self.tmp) / name
        path.write_bytes(b"fake")
        return str(path)

    def test_empty_library_opens_file_browser_directly(self):
        target = self._make_file("nen.png")
        QFileDialog.getOpenFileName = staticmethod(lambda *a, **k: (target, ""))
        program = Program()

        result = pick_file(None, program, self.button, "image")

        self.assertEqual(result, target)
        self.assertEqual(program.image_library, [target])

    def test_empty_library_cancel_returns_empty_and_remembers_nothing(self):
        QFileDialog.getOpenFileName = staticmethod(lambda *a, **k: ("", ""))
        program = Program()

        result = pick_file(None, program, self.button, "ppt")

        self.assertEqual(result, "")
        self.assertEqual(program.ppt_library, [])

if __name__ == "__main__":
    unittest.main()
