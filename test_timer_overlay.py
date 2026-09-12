import unittest

from PySide6.QtWidgets import QApplication

from timer_overlay import TimerOverlay


class TimerOverlayTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.overlay = TimerOverlay()
        self.addCleanup(self.overlay.close)

    def test_start_sets_initial_countdown(self):
        self.overlay.start(15)
        self.assertEqual(self.overlay.remaining_seconds, 15 * 60)
        self.assertEqual(self.overlay.label.text(), "15:00")
        self.assertTrue(self.overlay.timer.isActive())

    def test_tick_counts_down(self):
        self.overlay.start(1)
        self.overlay._tick()
        self.assertEqual(self.overlay.remaining_seconds, 59)
        self.assertEqual(self.overlay.label.text(), "00:59")

    def test_goes_into_overtime_with_minus_sign(self):
        self.overlay.start(0)
        self.overlay._tick()
        self.assertEqual(self.overlay.remaining_seconds, -1)
        self.assertEqual(self.overlay.label.text(), "-00:01")

    def test_stop_hides_and_stops_timer(self):
        self.overlay.start(5)
        self.overlay.stop()
        self.assertFalse(self.overlay.timer.isActive())


if __name__ == "__main__":
    unittest.main()
