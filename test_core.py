import tempfile
import unittest
from pathlib import Path

from core import Program, Report


class ProgramTest(unittest.TestCase):
    def test_scene_order(self):
        program = Program(reports=[Report(name="A"), Report(name="B")])
        self.assertEqual(
            [scene["type"] for scene in program.scenes()],
            [
                "opening", "speaker", "powerpoint", "transition",
                "speaker", "powerpoint", "transition",
                "discussion", "post_test", "closing",
            ],
        )

    def test_round_trip_json(self):
        program = Program(event_name="Hội nghị", reports=[Report(name="Báo cáo viên")])
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "program.json"
            program.save(str(path))
            loaded = Program.load(str(path))
        self.assertEqual(loaded.event_name, "Hội nghị")
        self.assertEqual(loaded.reports[0].name, "Báo cáo viên")


if __name__ == "__main__":
    unittest.main()
