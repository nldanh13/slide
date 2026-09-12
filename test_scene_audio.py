import shutil
import tempfile
import unittest
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox

from core import Report


class FakeAudioController:
    def __init__(self):
        self.playing_path = None
        self.play_calls: list[str] = []
        self.stop_calls = 0

    def play_loop(self, path):
        self.playing_path = path
        self.play_calls.append(path)

    def stop(self):
        self.playing_path = None
        self.stop_calls += 1


class SceneAudioTest(unittest.TestCase):
    """Nhạc nền chỉ phát khi chờ khai mạc / giải lao thảo luận / kết thúc — tắt khi
    có báo cáo viên đang trình bày (giới thiệu, PowerPoint) hoặc chuyển tiếp."""

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
        self.music_path = str(Path(self.tmp) / "nhac.mp3")
        Path(self.music_path).write_bytes(b"fake")
        self.ppt_path = str(Path(self.tmp) / "bai.pptx")
        Path(self.ppt_path).write_bytes(b"fake")

        self.window = MainWindow()
        self.addCleanup(self.window.remote.stop)
        self.addCleanup(self.window.close)

        self.audio = FakeAudioController()
        self.window.audio = self.audio

        self.running = False
        self.window.ppt.start = lambda path: setattr(self, "running", True)
        self.window.ppt.is_running = lambda: self.running
        self.window.ppt.close_presentation = lambda: setattr(self, "running", False)

        self.window.event_name.setText("Sự kiện test")
        self.window.program.background_music = self.music_path
        self.window.program.reports = [Report(name="A", topic="T", ppt=self.ppt_path)]
        self.window._refresh_table()

    def _advance(self, times: int) -> None:
        for _ in range(times):
            self.window.next_scene()
            self.app.processEvents()

    def test_music_plays_on_opening_scene(self):
        self.window.start_show()
        self.app.processEvents()
        self.assertEqual(self.window.scenes[self.window.scene_index]["type"], "opening")
        self.assertEqual(self.audio.playing_path, self.music_path)

    def test_music_stops_on_speaker_intro(self):
        self.window.start_show()
        self._advance(1)
        self.assertEqual(self.window.scenes[self.window.scene_index]["type"], "speaker")
        self.assertIsNone(self.audio.playing_path)

    def test_music_stops_during_powerpoint(self):
        self.window.start_show()
        self._advance(2)
        self.assertEqual(self.window.scenes[self.window.scene_index]["type"], "powerpoint")
        self.assertIsNone(self.audio.playing_path)

    def test_music_resumes_on_discussion(self):
        self.window.start_show()
        self._advance(4)
        self.assertEqual(self.window.scenes[self.window.scene_index]["type"], "discussion")
        self.assertEqual(self.audio.playing_path, self.music_path)

    def test_music_stops_on_post_test(self):
        self.window.start_show()
        self._advance(5)
        self.assertEqual(self.window.scenes[self.window.scene_index]["type"], "post_test")
        self.assertIsNone(self.audio.playing_path)

    def test_music_plays_on_closing(self):
        self.window.start_show()
        self._advance(6)
        self.assertEqual(self.window.scenes[self.window.scene_index]["type"], "closing")
        self.assertEqual(self.audio.playing_path, self.music_path)

    def test_music_stops_when_show_is_stopped(self):
        self.window.start_show()
        self.window.stop_show()
        self.assertIsNone(self.audio.playing_path)

    def test_no_music_configured_never_calls_play(self):
        self.window.program.background_music = ""
        self.window.start_show()
        self.app.processEvents()
        self.assertEqual(self.audio.play_calls, [])


if __name__ == "__main__":
    unittest.main()
