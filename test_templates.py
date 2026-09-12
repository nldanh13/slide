import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import templates
from core import Program, Report


class TemplatesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        patcher = mock.patch.object(templates, "TEMPLATES_DIR", Path(self.tmp) / "templates")
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_list_is_empty_when_no_templates_dir(self):
        self.assertEqual(templates.list_templates(), [])

    def test_save_then_list_and_load(self):
        program = Program(event_name="Hội nghị", reports=[Report(name="A", topic="T", ppt="core.py")])
        templates.save_template("Mẫu 1", program)
        self.assertEqual(templates.list_templates(), ["Mẫu 1"])
        self.assertTrue(templates.template_exists("Mẫu 1"))
        loaded = templates.load_template("Mẫu 1")
        self.assertEqual(loaded.event_name, "Hội nghị")
        self.assertEqual(loaded.reports[0].name, "A")

    def test_delete_template(self):
        templates.save_template("Tam", Program())
        templates.delete_template("Tam")
        self.assertEqual(templates.list_templates(), [])

    def test_delete_missing_template_does_not_raise(self):
        templates.delete_template("khong ton tai")

    def test_empty_name_is_rejected(self):
        with self.assertRaises(templates.TemplateNameError):
            templates.save_template("   ***   ", Program())

    def test_path_traversal_name_is_sanitized_and_stays_inside_templates_dir(self):
        templates.save_template("../../etc/passwd", Program())
        for name in templates.list_templates():
            self.assertNotIn("/", name)
            self.assertNotIn("..", name)
        saved_files = list(templates.TEMPLATES_DIR.glob("*.json"))
        for path in saved_files:
            self.assertEqual(path.resolve().parent, templates.TEMPLATES_DIR.resolve())

    def test_load_missing_template_raises(self):
        from core import ProgramFileError

        with self.assertRaises(ProgramFileError):
            templates.load_template("khong ton tai")


if __name__ == "__main__":
    unittest.main()
