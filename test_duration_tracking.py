import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox

from core import Report


class DurationTrackingTest(unittest.TestCase):
    """Theo dõi thời gian thực tế mỗi báo cáo viên trình bày (dùng cho báo cáo
    thời lượng sau chương trình) — dựa trên self._now() thay vì time.monotonic()
    trực tiếp để test kiểm soát được thời gian trôi qua."""

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
        self.window.ppt.current_slide_number = lambda: 0

        self._clock = 1000.0
        self.window._now = lambda: self._clock

        self.window.event_name.setText("Sự kiện test")
        self.report_a = Report(name="A", topic="T1", ppt=self.ppt_path, duration_minutes=15)
        self.report_b = Report(name="B", topic="T2", ppt=self.ppt_path, duration_minutes=10)
        self.window.program.reports = [self.report_a, self.report_b]
        self.window._refresh_table()

    def _advance_clock(self, seconds: float) -> None:
        self._clock += seconds

    def test_seconds_accumulated_after_leaving_powerpoint_scene(self):
        self.window.start_show()
        self.window.next_scene()  # -> speaker A
        self.window.next_scene()  # -> powerpoint A (bắt đầu tính giờ)
        self._advance_clock(125)
        self.window.next_scene()  # -> transition A (kết thúc tính giờ)
        self.assertAlmostEqual(self.window._actual_seconds[id(self.report_a)], 125, places=3)

    def test_no_entry_recorded_before_leaving_scene(self):
        self.window.start_show()
        self.window.next_scene()
        self.window.next_scene()
        self._advance_clock(60)
        self.assertNotIn(id(self.report_a), self.window._actual_seconds)

    def test_stopping_mid_presentation_records_elapsed_time(self):
        self.window.start_show()
        self.window.next_scene()
        self.window.next_scene()
        self._advance_clock(40)
        self.window.stop_show()
        self.assertAlmostEqual(self.window._actual_seconds[id(self.report_a)], 40, places=3)

    def test_auto_advance_when_ppt_closes_itself_records_time(self):
        self.window.start_show()
        self.window.next_scene()
        self.window.next_scene()
        self.window._monitor_powerpoint()  # ghi nhận ppt_seen_running=True trong lúc đang chạy
        self._advance_clock(90)
        self.running = False  # báo cáo viên tự thoát PowerPoint (Esc)
        self.window._monitor_powerpoint()
        self.assertAlmostEqual(self.window._actual_seconds[id(self.report_a)], 90, places=3)

    def test_restarting_show_resets_previous_totals(self):
        self.window.start_show()
        self.window.next_scene()
        self.window.next_scene()
        self._advance_clock(30)
        self.window.next_scene()
        self.assertIn(id(self.report_a), self.window._actual_seconds)

        self.window.start_show()
        self.assertEqual(self.window._actual_seconds, {})

    def test_export_duration_report_without_data_shows_info_message(self):
        with mock.patch.object(QMessageBox, "information") as info:
            self.window.export_duration_report()
        info.assert_called_once()

    def test_export_duration_report_with_data_writes_file(self):
        self.window.start_show()
        self.window.next_scene()
        self.window.next_scene()
        self._advance_clock(50)
        self.window.next_scene()

        out_path = str(Path(self.tmp) / "report.pdf")
        with mock.patch.object(QFileDialog, "getSaveFileName", return_value=(out_path, "")):
            self.window.export_duration_report()
        self.assertTrue(Path(out_path).is_file())


if __name__ == "__main__":
    unittest.main()
