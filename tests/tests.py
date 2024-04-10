import unittest

from whisper_cpu.app import Model, main


class TestModel(unittest.TestCase):
    def test_en(self):
        test_file_en = "test_en.mp3"
        test_transcript, no_ts_test_transcript, file_tr, no_file_tr = main(
            "English", test_file_en
        )
        self.assertIn(
            "Today, in the world of freedom, the proudest boast is", test_transcript
        )
        self.assertIn(
            "Today, in the world of freedom, the proudest boast is",
            no_ts_test_transcript,
        )
        with open(file_tr, "r") as f_tr:
            self.assertEqual(f_tr.read(), test_transcript)
        with open(no_file_tr, "r") as f_no_tr:
            self.assertEqual(f_no_tr.read(), no_ts_test_transcript)

    def test_fr(self):
        test_file_en = "test_fr.ogg"
        test_transcript, no_ts_test_transcript, file_tr, no_file_tr = main(
            "French", test_file_en
        )
        self.assertIn("La goutte d'eau qui fait déborder le vase", test_transcript)
        self.assertIn(
            "La goutte d'eau qui fait déborder le vase",
            no_ts_test_transcript,
        )
        with open(file_tr, "r") as f_tr:
            self.assertEqual(f_tr.read(), test_transcript)
        with open(no_file_tr, "r") as f_no_tr:
            self.assertEqual(f_no_tr.read(), no_ts_test_transcript)

    def test_multi(self):
        test_file_en = "test_en.mp3"
        test_transcript, no_ts_test_transcript, file_tr, no_file_tr = main(
            "Multilingual", test_file_en
        )
        self.assertIn(
            "Today, in the world of freedom, the proudest boast is", test_transcript
        )
        self.assertIn(
            "Today, in the world of freedom, the proudest boast is",
            no_ts_test_transcript,
        )
        self.assertIn("Ich bin ein ", test_transcript)
        self.assertIn(
            "Ich bin ein ",
            no_ts_test_transcript,
        )
        with open(file_tr, "r") as f_tr:
            self.assertEqual(f_tr.read(), test_transcript)
        with open(no_file_tr, "r") as f_no_tr:
            self.assertEqual(f_no_tr.read(), no_ts_test_transcript)

    def test_invalid_language(self):
        test_file_en = "test_en.mp3"
        test_transcript, no_ts_test_transcript, file_tr, no_file_tr = main(
            "Dummy", test_file_en
        )

        self.assertIn(
            "Today, in the world of freedom, the proudest boast is", test_transcript
        )
        self.assertIn(
            "Today, in the world of freedom, the proudest boast is",
            no_ts_test_transcript,
        )
        with open(file_tr, "r") as f_tr:
            self.assertEqual(f_tr.read(), test_transcript)
        with open(no_file_tr, "r") as f_no_tr:
            self.assertEqual(f_no_tr.read(), no_ts_test_transcript)
        dummy_model = Model("Dummy")
        self.assertEqual(dummy_model.language, "Dummy")
        dummy_model.model
        self.assertEqual(dummy_model.language, "en")


if __name__ == "__main__":
    unittest.main()
