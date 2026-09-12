import unittest

import i18n


class TranslationTest(unittest.TestCase):
    def tearDown(self):
        i18n.set_language("vi")

    def test_default_language_is_vietnamese(self):
        self.assertEqual(i18n.get_language(), "vi")
        self.assertEqual(i18n.tr("Lưu"), "Lưu")

    def test_switch_to_english_translates_known_key(self):
        i18n.set_language("en")
        self.assertEqual(i18n.get_language(), "en")
        self.assertEqual(i18n.tr("Lưu"), "Save")

    def test_unknown_key_falls_back_to_source_text(self):
        i18n.set_language("en")
        self.assertEqual(i18n.tr("Chuỗi không có trong từ điển"), "Chuỗi không có trong từ điển")

    def test_invalid_language_code_is_ignored(self):
        i18n.set_language("fr")
        self.assertEqual(i18n.get_language(), "vi")

    def test_templated_strings_translate_before_formatting(self):
        i18n.set_language("en")
        template = i18n.tr("Đã lưu: {path}")
        self.assertEqual(template.format(path="a.json"), "Saved: a.json")


if __name__ == "__main__":
    unittest.main()
