import unittest

from bulk_import import classify_ppt_filename, guess_report_name


class ClassifyFilenameTest(unittest.TestCase):
    def test_plain_speaker_filename(self):
        self.assertEqual(classify_ppt_filename("BS_Nguyen_Van_A_ung_thu.pptx"), "speaker")

    def test_opening_keyword_with_underscores(self):
        self.assertEqual(classify_ppt_filename("01_Chuong_trinh_khai_mac.pptx"), "opening")

    def test_opening_keyword_with_diacritics(self):
        self.assertEqual(classify_ppt_filename("Khai mạc hội nghị.pptx"), "opening")

    def test_closing_keyword(self):
        self.assertEqual(classify_ppt_filename("Ket_thuc_be_mac.pptx"), "closing")

    def test_closing_keyword_english(self):
        self.assertEqual(classify_ppt_filename("closing_ceremony.pptx"), "closing")

    def test_mc_filename_is_interface_opening(self):
        self.assertEqual(classify_ppt_filename("MC_dan_chuong_trinh.pptx"), "opening")

    def test_numbered_speaker_filename(self):
        self.assertEqual(classify_ppt_filename("bai_bao_cao_2.pptx"), "speaker")


class GuessReportNameTest(unittest.TestCase):
    def test_replaces_underscores_and_capitalizes(self):
        self.assertEqual(guess_report_name("BS_Nguyen_Van_A.pptx"), "Bs Nguyen Van A")

    def test_replaces_dashes(self):
        self.assertEqual(guess_report_name("bao-cao-so-1.pptx"), "Bao Cao So 1")

    def test_empty_stem_returns_stem(self):
        self.assertEqual(guess_report_name("___.pptx"), "___")


if __name__ == "__main__":
    unittest.main()
