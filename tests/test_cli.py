import unittest

import click

from melo.main import resolve_speaker_id


class CliSpeakerTests(unittest.TestCase):
    def test_default_uses_first_model_speaker(self):
        self.assertEqual(resolve_speaker_id({"EN-Newest": 4}), 4)

    def test_speaker_names_accept_case_and_separator_variants(self):
        speakers = {"EN_INDIA": 3, "EN-BR": 2}

        self.assertEqual(resolve_speaker_id(speakers, "en-india"), 3)
        self.assertEqual(resolve_speaker_id(speakers, "en_br"), 2)

    def test_unknown_speaker_lists_model_choices(self):
        with self.assertRaisesRegex(click.BadParameter, "EN-Newest"):
            resolve_speaker_id({"EN-Newest": 4}, "EN-Default")


if __name__ == "__main__":
    unittest.main()
