import tempfile
import unittest
from pathlib import Path

from PySide6.QtWidgets import QApplication

from core import Program, Report
from export_schedule import build_duration_report_html, export_duration_report_pdf


class BuildDurationReportHtmlTest(unittest.TestCase):
    def test_includes_planned_and_actual_minutes(self):
        report = Report(name="BS A", duration_minutes=15)
        program = Program(event_name="Hoi nghi", reports=[report])
        html = build_duration_report_html(program, {id(report): 20 * 60})
        self.assertIn("BS A", html)
        self.assertIn(">15<", html)
        self.assertIn("20.0", html)
        self.assertIn("+5.0", html)

    def test_negative_difference_for_shorter_than_planned(self):
        report = Report(name="BS B", duration_minutes=20)
        program = Program(reports=[report])
        html = build_duration_report_html(program, {id(report): 12 * 60})
        self.assertIn("-8.0", html)

    def test_report_without_recorded_time_shows_zero(self):
        report = Report(name="BS C", duration_minutes=10)
        program = Program(reports=[report])
        html = build_duration_report_html(program, {})
        self.assertIn("0.0", html)

    def test_no_reports_shows_placeholder_row(self):
        program = Program(reports=[])
        html = build_duration_report_html(program, {})
        self.assertIn("Chưa có báo cáo viên", html)


class ExportDurationReportPdfTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_writes_pdf_file(self):
        report = Report(name="BS A", duration_minutes=15)
        program = Program(reports=[report])
        with tempfile.TemporaryDirectory() as folder:
            path = str(Path(folder) / "report.pdf")
            export_duration_report_pdf(program, {id(report): 900}, path)
            self.assertTrue(Path(path).is_file())
            self.assertGreater(Path(path).stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
