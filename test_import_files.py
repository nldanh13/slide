import shutil
import tempfile
import unittest
from pathlib import Path

from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox


class ImportFilesTest(unittest.TestCase):
    """Luồng nhập file gộp (thay cho '+ Thêm báo cáo viên' và 'Nhập nhiều file
    PowerPoint' cũ): 1 nút duy nhất, phân loại tự động, áp dụng thẳng vào
    chương trình — không qua dialog xem trước riêng."""

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls._orig_question = QMessageBox.question
        QMessageBox.question = staticmethod(lambda *a, **k: QMessageBox.Yes)

    @classmethod
    def tearDownClass(cls):
        QMessageBox.question = cls._orig_question

    def setUp(self):
        from main_window import MainWindow

        self.window = MainWindow()
        self.addCleanup(self.window.remote.stop)
        self.addCleanup(self.window.close)

        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

        self._orig_get_open_file_names = QFileDialog.getOpenFileNames
        self.addCleanup(setattr, QFileDialog, "getOpenFileNames", self._orig_get_open_file_names)
        self._orig_get_open_file_name = QFileDialog.getOpenFileName
        self.addCleanup(setattr, QFileDialog, "getOpenFileName", self._orig_get_open_file_name)

    def _make_file(self, name: str) -> str:
        path = Path(self.tmp) / name
        path.write_bytes(b"fake")
        return str(path)

    def _import(self, filenames):
        paths = [self._make_file(name) for name in filenames]
        QFileDialog.getOpenFileNames = staticmethod(lambda *a, **k: (paths, ""))
        self.window.import_files()
        self.app.processEvents()
        return paths

    def test_cancel_does_nothing(self):
        QFileDialog.getOpenFileNames = staticmethod(lambda *a, **k: ([], ""))
        self.window.import_files()
        self.assertEqual(self.window.program.reports, [])

    def test_speaker_ppt_becomes_report_row(self):
        self._import(["BS_Nguyen_Van_A.pptx"])
        self.assertEqual(len(self.window.program.reports), 1)
        self.assertEqual(self.window.program.reports[0].name, "Bs Nguyen Van A")
        self.assertEqual(self.window.table.rowCount(), 1)

    def test_opening_and_closing_ppt_fill_interface_fields(self):
        self._import(["Khai_mac_hoi_nghi.pptx", "Ket_thuc_be_mac.pptx"])
        self.assertTrue(self.window.program.opening_ppt.endswith("Khai_mac_hoi_nghi.pptx"))
        self.assertTrue(self.window.program.closing_ppt.endswith("Ket_thuc_be_mac.pptx"))
        self.assertEqual(self.window.program.reports, [])

    def test_images_fill_dedicated_role_fields(self):
        self._import(["thao_luan.png", "post_test_slide.jpg", "anh_ket_thuc.png"])
        self.assertTrue(self.window.program.discussion_image.endswith("thao_luan.png"))
        self.assertTrue(self.window.program.post_test_image.endswith("post_test_slide.jpg"))
        self.assertTrue(self.window.program.closing_image.endswith("anh_ket_thuc.png"))

    def test_unmatched_image_defaults_to_background(self):
        self._import(["random_photo.jpg"])
        self.assertTrue(self.window.program.background.endswith("random_photo.jpg"))

    def test_mixed_batch_speaker_and_interface_together(self):
        self._import(["BS_A.pptx", "BS_B.pptx", "Khai_mac.pptx", "nen.png"])
        self.assertEqual(len(self.window.program.reports), 2)
        self.assertTrue(self.window.program.opening_ppt.endswith("Khai_mac.pptx"))
        self.assertTrue(self.window.program.background.endswith("nen.png"))

    def test_interface_table_reflects_current_assignments(self):
        self._import(["Khai_mac.pptx"])
        # Hàng 0 trong INTERFACE_SLOTS là "opening_ppt" -> "Mở đầu (PowerPoint)"
        self.assertEqual(self.window.interface_table.item(0, 1).text(), "Khai_mac.pptx")
        # Hàng chưa gán vẫn hiện "Chưa chọn"
        self.assertEqual(self.window.interface_table.item(1, 1).text(), "Chưa chọn")

    def test_choose_and_clear_interface_file_updates_program_and_table(self):
        target = self._make_file("custom_background.png")
        QFileDialog.getOpenFileName = staticmethod(lambda *a, **k: (target, ""))
        self.window._choose_interface_file("background", "image")
        self.assertEqual(self.window.program.background, target)
        self.assertEqual(self.window.interface_table.item(1, 1).text(), "custom_background.png")

        self.window._clear_interface_file("background")
        self.assertEqual(self.window.program.background, "")
        self.assertEqual(self.window.interface_table.item(1, 1).text(), "Chưa chọn")


if __name__ == "__main__":
    unittest.main()
