import unittest

from melo.text.english_utils.normalization import normalize_english_tokens


class EnglishTokenNormalizationTests(unittest.TestCase):
    def test_uppercase_initialism_uses_unambiguous_letter_names(self):
        self.assertEqual(
            normalize_english_tokens("US paused shipment of bombs"),
            "you ess paused shipment of bombs",
        )

    def test_lowercase_word_is_preserved(self):
        self.assertEqual(normalize_english_tokens("Please tell us"), "Please tell us")

    def test_mixed_language_technical_terms_are_expanded(self):
        self.assertEqual(
            normalize_english_tokens("NLP、ChatGPT、LLM、AI、AIGC、SDXL、ControlNet"),
            (
                "en el pee、Chat gee pee tee、el el em、ay eye、"
                "ay eye gee cee、ess dee ex el、Control Net"
            ),
        )

    def test_acronym_before_title_case_word_gets_a_boundary(self):
        self.assertEqual(
            normalize_english_tokens("HTTPServer"),
            "aitch tee tee pee Server",
        )


if __name__ == "__main__":
    unittest.main()
