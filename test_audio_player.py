import shutil
import tempfile
import unittest
from pathlib import Path

from audio_player import AudioController


class FakePlayer:
    def __init__(self):
        self.audio_output = None
        self.source = None
        self.loops = None
        self.played = False
        self.stopped = False

    def setAudioOutput(self, output):
        self.audio_output = output

    def setSource(self, url):
        self.source = url

    def setLoops(self, loops):
        self.loops = loops

    def play(self):
        self.played = True

    def stop(self):
        self.stopped = True


class FakeAudioOutput:
    def __init__(self):
        self.volume = None

    def setVolume(self, volume):
        self.volume = volume


class AudioControllerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.created_players: list[FakePlayer] = []
        self.created_outputs: list[FakeAudioOutput] = []

        def factory():
            player = FakePlayer()
            output = FakeAudioOutput()
            self.created_players.append(player)
            self.created_outputs.append(output)
            return player, output

        self.controller = AudioController(player_factory=factory)

    def _make_file(self, name: str) -> str:
        path = Path(self.tmp) / name
        path.write_bytes(b"fake")
        return str(path)

    def test_play_loop_starts_playback(self):
        path = self._make_file("nhac.mp3")
        self.controller.play_loop(path)
        self.assertEqual(len(self.created_players), 1)
        self.assertTrue(self.created_players[0].played)
        self.assertEqual(self.created_players[0].loops, -1)

    def test_play_loop_same_path_does_not_restart(self):
        path = self._make_file("nhac.mp3")
        self.controller.play_loop(path)
        self.controller.play_loop(path)
        self.assertEqual(len(self.created_players), 1)
        self.assertFalse(self.created_players[0].stopped)

    def test_play_loop_different_path_restarts(self):
        path1 = self._make_file("a.mp3")
        path2 = self._make_file("b.mp3")
        self.controller.play_loop(path1)
        self.controller.play_loop(path2)
        self.assertEqual(len(self.created_players), 2)
        self.assertTrue(self.created_players[0].stopped)
        self.assertTrue(self.created_players[1].played)

    def test_missing_file_does_not_start_playback(self):
        self.controller.play_loop(str(Path(self.tmp) / "khong_ton_tai.mp3"))
        self.assertEqual(self.created_players, [])
        self.assertIsNone(self.controller.player)

    def test_empty_path_stops_current_playback(self):
        path = self._make_file("nhac.mp3")
        self.controller.play_loop(path)
        self.controller.play_loop("")
        self.assertTrue(self.created_players[0].stopped)
        self.assertIsNone(self.controller.player)

    def test_stop_clears_state(self):
        path = self._make_file("nhac.mp3")
        self.controller.play_loop(path)
        self.controller.stop()
        self.assertIsNone(self.controller.player)
        self.assertIsNone(self.controller.audio_output)
        self.assertTrue(self.created_players[0].stopped)

    def test_stop_without_playback_does_not_error(self):
        self.controller.stop()
        self.assertIsNone(self.controller.player)

    def test_is_playing_reflects_state(self):
        self.assertFalse(self.controller.is_playing())
        path = self._make_file("nhac.mp3")
        self.controller.play_loop(path)
        self.assertTrue(self.controller.is_playing())
        self.controller.stop()
        self.assertFalse(self.controller.is_playing())

    def test_new_playback_uses_last_set_volume(self):
        self.controller.set_volume(0.3)
        path = self._make_file("nhac.mp3")
        self.controller.play_loop(path)
        self.assertAlmostEqual(self.created_outputs[0].volume, 0.3)

    def test_set_volume_applies_live_while_playing(self):
        path = self._make_file("nhac.mp3")
        self.controller.play_loop(path)
        self.controller.set_volume(0.9)
        self.assertAlmostEqual(self.created_outputs[0].volume, 0.9)

    def test_set_volume_is_clamped_to_valid_range(self):
        self.controller.set_volume(1.5)
        path = self._make_file("nhac.mp3")
        self.controller.play_loop(path)
        self.assertAlmostEqual(self.created_outputs[0].volume, 1.0)

        self.controller.set_volume(-0.5)
        self.assertAlmostEqual(self.created_outputs[0].volume, 0.0)


if __name__ == "__main__":
    unittest.main()
