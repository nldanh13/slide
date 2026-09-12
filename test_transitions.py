import unittest

from PySide6.QtWidgets import QApplication, QMessageBox

from core import Report


class SceneTransitionOrderingTest(unittest.TestCase):
    """Đảm bảo màn hình sân khấu luôn được hiện/chuẩn bị nội dung TRƯỚC khi đóng
    PowerPoint hiện tại, và chỉ ẩn đi SAU khi PowerPoint kế tiếp đã thật sự chạy —
    đây là phần cốt lõi giảm hiện tượng nháy màn hình giữa các bài báo cáo."""

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls._orig_warning = QMessageBox.warning
        cls._orig_critical = QMessageBox.critical
        cls._orig_question = QMessageBox.question
        QMessageBox.warning = staticmethod(lambda *a, **k: QMessageBox.Ok)
        QMessageBox.critical = staticmethod(lambda *a, **k: QMessageBox.Ok)
        QMessageBox.question = staticmethod(lambda *a, **k: QMessageBox.Yes)

    @classmethod
    def tearDownClass(cls):
        QMessageBox.warning = cls._orig_warning
        QMessageBox.critical = cls._orig_critical
        QMessageBox.question = cls._orig_question

    def setUp(self):
        from main_window import MainWindow

        self.window = MainWindow()
        self.addCleanup(self.window.remote.stop)
        self.addCleanup(self.window.close)

        self.running = False
        self.window.ppt.start = lambda path: setattr(self, "running", True)
        self.window.ppt.is_running = lambda: self.running
        self.window.ppt.close_presentation = lambda: setattr(self, "running", False)

        self.window.event_name.setText("Sự kiện test")
        self.window.program.reports = [
            Report(name="A", topic="T1", ppt="core.py"),
            Report(name="B", topic="T2", ppt="core.py"),
        ]
        self.window._refresh_table()
        self.window.start_show()
        self.app.processEvents()
        # đưa tới scene "speaker" đầu tiên rồi tới "powerpoint"
        self.window.next_scene()
        self.window.next_scene()
        self.app.processEvents()
        self.assertEqual(self.window.scenes[self.window.scene_index]["type"], "powerpoint")

    def test_stage_not_hidden_immediately_when_powerpoint_starts(self):
        self.assertTrue(self.window.stage.isVisible())
        self.assertTrue(self.window._pending_ppt_hide_stage)

    def test_stage_hidden_only_after_powerpoint_confirmed_running(self):
        self.running = True
        self.window._monitor_powerpoint()
        self.assertFalse(self.window.stage.isVisible())
        self.assertFalse(self.window._pending_ppt_hide_stage)

    def test_stage_shown_with_next_content_before_close_on_manual_next(self):
        self.running = True
        self.window._monitor_powerpoint()  # ppt confirmed running, stage hidden

        seen = {}

        def tracked_close():
            seen["stage_visible_at_close"] = self.window.stage.isVisible()
            self.running = False

        self.window.ppt.close_presentation = tracked_close
        self.window.next_scene()

        self.assertTrue(seen.get("stage_visible_at_close"))
        self.assertEqual(self.window.scenes[self.window.scene_index]["type"], "transition")

    def test_stage_shown_with_next_content_before_close_on_auto_advance(self):
        self.running = True
        self.window._monitor_powerpoint()  # ppt confirmed running, stage hidden

        seen = {}

        def tracked_close():
            seen["stage_visible_at_close"] = self.window.stage.isVisible()
            self.running = False

        self.window.ppt.close_presentation = tracked_close

        # báo cáo viên tự bấm Esc trong PowerPoint -> is_running() chuyển False
        self.running = False
        self.window._monitor_powerpoint()

        self.assertTrue(seen.get("stage_visible_at_close"))
        self.assertEqual(self.window.scenes[self.window.scene_index]["type"], "transition")


if __name__ == "__main__":
    unittest.main()
