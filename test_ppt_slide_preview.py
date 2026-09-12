import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from PySide6.QtWidgets import QApplication, QMessageBox

from core import Report
from slide_export import SlideExportError


class PollPptSlidePreviewTest(unittest.TestCase):
    """_poll_ppt_slide_preview() mirror slide PowerPoint thật (qua COM) vào khung
    xem trước — chỉ xuất ảnh khi số slide thực sự thay đổi, để tránh gọi COM (rất
    tốn kém) lặp lại cho cùng 1 slide."""

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

        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.ppt_path = str(Path(self.tmp) / "bai.pptx")
        Path(self.ppt_path).write_bytes(b"fake")

        self.window = MainWindow()
        self.addCleanup(self.window.remote.stop)
        self.addCleanup(self.window.close)

        self.running = False
        self.window.ppt.start = lambda path: setattr(self, "running", True)
        self.window.ppt.is_running = lambda: self.running
        self.window.ppt.close_presentation = lambda: setattr(self, "running", False)
        self.window.ppt.current_slide_number = lambda: self.slide_number
        self.slide_number = 0

        self.window.event_name.setText("Sự kiện test")
        self.window.program.reports = [Report(name="A", topic="T", ppt=self.ppt_path)]
        self.window._refresh_table()
        self.window.start_show()
        self.window.next_scene()  # -> speaker
        self.window.next_scene()  # -> powerpoint (calls ppt.start, resets slide tracking)
        self.app.processEvents()
        self.assertEqual(self.window.scenes[self.window.scene_index]["type"], "powerpoint")

    def test_first_slide_change_exports_and_updates_preview(self):
        self.slide_number = 1
        with mock.patch("main_window.export_slide_image", return_value="/exported/1.png") as export:
            self.window._poll_ppt_slide_preview()
        export.assert_called_once_with(self.ppt_path, 1)
        self.assertEqual(self.window.preview_pane.background_path, "/exported/1.png")

    def test_same_slide_number_does_not_reexport(self):
        self.slide_number = 1
        with mock.patch("main_window.export_slide_image", return_value="/exported/1.png") as export:
            self.window._poll_ppt_slide_preview()
            self.window._poll_ppt_slide_preview()
        export.assert_called_once()

    def test_slide_number_zero_is_ignored(self):
        self.slide_number = 0
        with mock.patch("main_window.export_slide_image") as export:
            self.window._poll_ppt_slide_preview()
        export.assert_not_called()

    def test_export_error_does_not_crash(self):
        self.slide_number = 2
        with mock.patch("main_window.export_slide_image", side_effect=SlideExportError("no ppt")):
            self.window._poll_ppt_slide_preview()  # không được ném lỗi ra ngoài

    def test_not_a_powerpoint_scene_is_a_no_op(self):
        self.window.next_scene()  # -> transition (rời khỏi cảnh powerpoint)
        self.app.processEvents()
        self.slide_number = 3
        with mock.patch.object(self.window.ppt, "current_slide_number") as poll:
            self.window._poll_ppt_slide_preview()
        poll.assert_not_called()

    def test_new_presentation_resets_slide_tracking(self):
        self.slide_number = 5
        with mock.patch("main_window.export_slide_image", return_value="/exported/5.png"):
            self.window._poll_ppt_slide_preview()
        self.assertEqual(self.window._last_previewed_slide, 5)

        # Báo cáo viên tiếp theo bắt đầu bài PowerPoint mới -> phải xuất lại slide 1
        # dù trùng số với slide cuối của bài trước, vì _show_current_scene() đã reset.
        self.window.program.reports.append(Report(name="B", topic="T2", ppt=self.ppt_path))
        self.window.scenes = self.window.program.scenes()
        self.window.scene_index = 5  # scene "powerpoint" của báo cáo viên thứ 2
        self.assertEqual(self.window.scenes[5]["type"], "powerpoint")
        self.window._show_current_scene()
        self.assertEqual(self.window._last_previewed_slide, 0)


if __name__ == "__main__":
    unittest.main()
