import tempfile
import unittest
from pathlib import Path

from core import Program, ProgramFileError, Report, validate_program


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

    def test_scene_order_with_no_reports(self):
        program = Program(reports=[])
        self.assertEqual(
            [scene["type"] for scene in program.scenes()],
            ["opening", "discussion", "post_test", "closing"],
        )

    def test_scene_order_with_opening_and_closing_ppt(self):
        program = Program(
            reports=[Report(name="A")],
            opening_ppt="opening.pptx",
            closing_ppt="closing.pptx",
        )
        scenes = program.scenes()
        self.assertEqual(scenes[0]["type"], "powerpoint")
        self.assertEqual(scenes[0]["interface_kind"], "opening")
        self.assertEqual(scenes[0]["report"].ppt, "opening.pptx")
        self.assertEqual(scenes[0]["report"].duration_minutes, 0)
        self.assertEqual(scenes[-1]["type"], "powerpoint")
        self.assertEqual(scenes[-1]["interface_kind"], "closing")
        self.assertEqual(scenes[-1]["report"].ppt, "closing.pptx")

    def test_round_trip_json(self):
        program = Program(event_name="Hội nghị", reports=[Report(name="Báo cáo viên")])
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "program.json"
            program.save(str(path))
            loaded = Program.load(str(path))
        self.assertEqual(loaded.event_name, "Hội nghị")
        self.assertEqual(loaded.reports[0].name, "Báo cáo viên")

    def test_load_missing_file_raises_program_file_error(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ProgramFileError):
                Program.load(str(Path(folder) / "khong_ton_tai.json"))

    def test_load_malformed_json_raises_program_file_error(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bad.json"
            path.write_text("{khong phai json hop le", encoding="utf-8")
            with self.assertRaises(ProgramFileError):
                Program.load(str(path))

    def test_load_unknown_field_raises_program_file_error(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bad.json"
            path.write_text('{"truong_khong_ton_tai": 1, "reports": []}', encoding="utf-8")
            with self.assertRaises(ProgramFileError):
                Program.load(str(path))

    def test_load_old_json_without_interface_ppt_fields_is_backward_compatible(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "old.json"
            path.write_text('{"event_name": "Cũ", "reports": []}', encoding="utf-8")
            loaded = Program.load(str(path))
        self.assertEqual(loaded.opening_ppt, "")
        self.assertEqual(loaded.closing_ppt, "")


class ValidateProgramTest(unittest.TestCase):
    def test_valid_program_has_no_errors(self):
        program = Program(
            event_name="Hội nghị",
            reports=[Report(name="A", topic="Chuyên đề", ppt=__file__)],
        )
        self.assertEqual(validate_program(program), [])

    def test_missing_event_name(self):
        program = Program(event_name="", reports=[Report(name="A", topic="T", ppt=__file__)])
        self.assertIn("Chưa nhập tên chương trình.", validate_program(program))

    def test_no_reports(self):
        program = Program(event_name="Hội nghị", reports=[])
        self.assertIn("Chưa có báo cáo viên.", validate_program(program))

    def test_missing_ppt_file_is_reported(self):
        program = Program(
            event_name="Hội nghị",
            reports=[Report(name="A", topic="T", ppt="khong_ton_tai.pptx")],
        )
        errors = validate_program(program)
        self.assertTrue(any("không tìm thấy" in e for e in errors))

    def test_missing_background_is_reported(self):
        program = Program(
            event_name="Hội nghị",
            background="khong_ton_tai.png",
            reports=[Report(name="A", topic="T", ppt=__file__)],
        )
        errors = validate_program(program)
        self.assertTrue(any("ảnh nền" in e for e in errors))

    def test_missing_speaker_photo_is_reported(self):
        program = Program(
            event_name="Hội nghị",
            reports=[Report(name="A", topic="T", ppt=__file__, photo="khong_ton_tai.png")],
        )
        errors = validate_program(program)
        self.assertTrue(any("khong_ton_tai.png" in e for e in errors))

    def test_missing_opening_ppt_is_reported(self):
        program = Program(
            event_name="Hội nghị",
            opening_ppt="khong_ton_tai.pptx",
            reports=[Report(name="A", topic="T", ppt=__file__)],
        )
        errors = validate_program(program)
        self.assertTrue(any("khai mạc" in e for e in errors))

    def test_missing_closing_ppt_is_reported(self):
        program = Program(
            event_name="Hội nghị",
            closing_ppt="khong_ton_tai.pptx",
            reports=[Report(name="A", topic="T", ppt=__file__)],
        )
        errors = validate_program(program)
        self.assertTrue(any("kết thúc" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
