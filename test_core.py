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

    def test_missing_name_and_topic_are_not_required(self):
        program = Program(
            event_name="Hội nghị",
            reports=[Report(name="", topic="", ppt=__file__)],
        )
        self.assertEqual(validate_program(program), [])

    def test_photo_slide_without_master_ppt_is_reported(self):
        program = Program(
            event_name="Hội nghị",
            reports=[Report(name="A", topic="T", ppt=__file__, photo_slide=2)],
        )
        errors = validate_program(program)
        self.assertTrue(any("chưa chọn file chương trình tổng" in e for e in errors))

    def test_missing_background_music_is_reported(self):
        program = Program(
            event_name="Hội nghị",
            background_music="khong_ton_tai.mp3",
            reports=[Report(name="A", topic="T", ppt=__file__)],
        )
        errors = validate_program(program)
        self.assertTrue(any("nhạc nền" in e for e in errors))

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

    def test_slide_assigned_without_master_ppt_is_reported(self):
        program = Program(
            event_name="Hội nghị",
            discussion_slide=3,
            reports=[Report(name="A", topic="T", ppt=__file__)],
        )
        errors = validate_program(program)
        self.assertTrue(any("file chương trình tổng" in e for e in errors))

    def test_missing_master_ppt_is_reported(self):
        program = Program(
            event_name="Hội nghị",
            master_ppt="khong_ton_tai.pptx",
            discussion_slide=1,
            reports=[Report(name="A", topic="T", ppt=__file__)],
        )
        errors = validate_program(program)
        self.assertTrue(any("chương trình tổng" in e and "khong_ton_tai.pptx" in e for e in errors))

    def test_missing_role_image_is_reported(self):
        program = Program(
            event_name="Hội nghị",
            closing_image="khong_ton_tai.png",
            reports=[Report(name="A", topic="T", ppt=__file__)],
        )
        errors = validate_program(program)
        self.assertTrue(any("Kết thúc" in e and "khong_ton_tai.png" in e for e in errors))

    def test_valid_with_existing_master_ppt_and_slides_has_no_extra_errors(self):
        program = Program(
            event_name="Hội nghị",
            master_ppt=__file__,
            background_slide=1,
            discussion_slide=2,
            reports=[Report(name="A", topic="T", ppt=__file__)],
        )
        errors = validate_program(program)
        self.assertEqual(errors, [])


class ProgramSlideHelpersTest(unittest.TestCase):
    def test_slide_config_for_returns_empty_when_unset(self):
        program = Program()
        self.assertEqual(program.slide_config_for("background"), ("", 0))

    def test_slide_config_for_returns_master_ppt_and_slide_number(self):
        program = Program(master_ppt="master.pptx", discussion_slide=4)
        self.assertEqual(program.slide_config_for("discussion"), ("master.pptx", 4))

    def test_slide_config_for_ignores_slide_without_master_ppt(self):
        program = Program(discussion_slide=4)
        self.assertEqual(program.slide_config_for("discussion"), ("", 0))


class RememberFileTest(unittest.TestCase):
    def test_ppt_file_goes_to_ppt_library(self):
        program = Program()
        program.remember_file("bai_bao_cao.pptx")
        self.assertEqual(program.ppt_library, ["bai_bao_cao.pptx"])
        self.assertEqual(program.image_library, [])

    def test_image_file_goes_to_image_library(self):
        program = Program()
        program.remember_file("nen.png")
        self.assertEqual(program.image_library, ["nen.png"])
        self.assertEqual(program.ppt_library, [])

    def test_audio_file_goes_to_audio_library(self):
        program = Program()
        program.remember_file("nhac_nen.mp3")
        self.assertEqual(program.audio_library, ["nhac_nen.mp3"])
        self.assertEqual(program.ppt_library, [])
        self.assertEqual(program.image_library, [])

    def test_unknown_extension_is_ignored(self):
        program = Program()
        program.remember_file("ghi_chu.txt")
        self.assertEqual(program.ppt_library, [])
        self.assertEqual(program.image_library, [])

    def test_empty_path_is_ignored(self):
        program = Program()
        program.remember_file("")
        self.assertEqual(program.ppt_library, [])
        self.assertEqual(program.image_library, [])

    def test_duplicate_path_is_not_added_twice(self):
        program = Program()
        program.remember_file("bai_bao_cao.pptx")
        program.remember_file("bai_bao_cao.pptx")
        self.assertEqual(program.ppt_library, ["bai_bao_cao.pptx"])

    def test_image_override_for_background_returns_background_field(self):
        program = Program(background="bg.png")
        self.assertEqual(program.image_override_for("background"), "bg.png")

    def test_image_override_for_other_roles(self):
        program = Program(post_test_image="pt.png")
        self.assertEqual(program.image_override_for("post_test"), "pt.png")
        self.assertEqual(program.image_override_for("closing"), "")


if __name__ == "__main__":
    unittest.main()
