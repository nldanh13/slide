import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import slide_export
from core import Program
from slide_export import SlideExportError, resolve_scene_image


class ResolveSceneImageTest(unittest.TestCase):
    def test_no_config_uses_background_directly(self):
        program = Program(background="bg.png")
        result = resolve_scene_image(program, "discussion", export=self.fail("should not be called"))
        self.assertEqual(result, "bg.png")

    def test_slide_configured_for_role_takes_priority(self):
        program = Program(background="bg.png", master_ppt="master.pptx", discussion_slide=5)
        calls = []

        def fake_export(ppt_path, slide_number):
            calls.append((ppt_path, slide_number))
            return f"/exported/{slide_number}.png"

        result = resolve_scene_image(program, "discussion", export=fake_export)
        self.assertEqual(result, "/exported/5.png")
        self.assertEqual(calls, [("master.pptx", 5)])

    def test_falls_back_to_dedicated_image_when_no_slide(self):
        program = Program(background="bg.png", discussion_image="discussion.png")
        result = resolve_scene_image(program, "discussion", export=self.fail("no slide configured"))
        self.assertEqual(result, "discussion.png")

    def test_falls_back_to_dedicated_image_when_export_fails(self):
        program = Program(
            background="bg.png", master_ppt="master.pptx", discussion_slide=5,
            discussion_image="discussion.png",
        )
        result = resolve_scene_image(program, "discussion", export=self.raise_error)
        self.assertEqual(result, "discussion.png")

    def test_falls_back_to_background_slide_when_role_export_fails_and_no_image(self):
        program = Program(background="bg.png", master_ppt="master.pptx", discussion_slide=5, background_slide=1)
        calls = []

        def export(ppt_path, slide_number):
            if slide_number == 5:
                raise SlideExportError("no ppt")
            calls.append((ppt_path, slide_number))
            return "/exported/1.png"

        result = resolve_scene_image(program, "discussion", export=export)
        self.assertEqual(result, "/exported/1.png")
        self.assertEqual(calls, [("master.pptx", 1)])

    def test_falls_back_to_plain_background_when_everything_fails(self):
        program = Program(background="bg.png", master_ppt="master.pptx", discussion_slide=5)
        result = resolve_scene_image(program, "discussion", export=self.raise_error)
        self.assertEqual(result, "bg.png")

    def test_background_role_used_for_opening_speaker_transition(self):
        program = Program(background="bg.png", master_ppt="master.pptx", background_slide=1)

        def export(ppt_path, slide_number):
            return f"/exported/{slide_number}.png"

        for scene_type in ("opening", "speaker", "transition"):
            self.assertEqual(resolve_scene_image(program, scene_type, export=export), "/exported/1.png")

    def test_unmapped_scene_type_uses_background_role(self):
        program = Program(background="bg.png")
        self.assertEqual(resolve_scene_image(program, "powerpoint", export=self.fail("n/a")), "bg.png")

    @staticmethod
    def raise_error(ppt_path, slide_number):
        raise SlideExportError("simulated failure")

    @staticmethod
    def fail(message):
        def _fail(*_args, **_kwargs):
            raise AssertionError(message)
        return _fail


class ExportSlideImageCacheTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        patcher = mock.patch.object(slide_export, "CACHE_DIR", Path(self.tmp) / "cache")
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_missing_ppt_file_raises(self):
        with self.assertRaises(SlideExportError):
            slide_export.export_slide_image(str(Path(self.tmp) / "khong_ton_tai.pptx"), 1)

    def test_cache_hit_returns_existing_file_without_com(self):
        ppt = Path(self.tmp) / "master.pptx"
        ppt.write_text("fake")
        cached = slide_export._cache_path(ppt, 2)
        cached.parent.mkdir(parents=True, exist_ok=True)
        cached.write_bytes(b"PNG")

        result = slide_export.export_slide_image(str(ppt), 2)
        self.assertEqual(result, str(cached))

    def test_prune_removes_stale_cache_for_same_slide(self):
        ppt = Path(self.tmp) / "master.pptx"
        ppt.write_text("fake")
        keep = slide_export._cache_path(ppt, 2)
        keep.parent.mkdir(parents=True, exist_ok=True)
        keep.write_bytes(b"NEW")
        stale = keep.parent / f"{ppt.stem}__111__2.png"
        stale.write_bytes(b"OLD")

        slide_export._prune_stale_cache(ppt, 2, keep)

        self.assertTrue(keep.is_file())
        self.assertFalse(stale.is_file())


if __name__ == "__main__":
    unittest.main()
