import unittest

from melo.text.english_utils.normalization import normalize_english_tokens
from melo.text.english_utils.pronunciation import (
    expand_informal_g_dropping,
    lookup_pronunciation,
)


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

    def test_dictionary_backed_informal_g_dropping_is_expanded(self):
        known_words = {"CHOKING", "JOKING", "RUNNING"}
        self.assertEqual(
            expand_informal_g_dropping(
                "He's chokin', everybody\u2019s jokin', and we're runnin'.",
                known_words,
            ),
            "He's choking, everybody\u2019s joking, and we're running.",
        )

    def test_valid_or_unknown_apostrophe_words_are_preserved(self):
        known_words = {"SIN", "SING"}
        self.assertEqual(
            expand_informal_g_dropping("sin' somethin'", known_words),
            "sin' somethin'",
        )

    def test_plugin_pronunciation_overrides_g2p_fallback(self):
        fallback = {"PLUGIN": (("P", "L", "UW1", "G"), ("IH0", "N"))}
        self.assertEqual(
            lookup_pronunciation("plugin", fallback),
            (("P", "L", "AH1", "G"), ("IH0", "N")),
        )
        self.assertEqual(
            lookup_pronunciation("plugins", {}),
            (("P", "L", "AH1", "G"), ("IH0", "N", "Z")),
        )

    def test_ordinary_dictionary_pronunciation_is_unchanged(self):
        fallback = {"HELLO": (("HH", "AH0"), ("L", "OW1"))}
        self.assertEqual(lookup_pronunciation("hello", fallback), fallback["HELLO"])


if __name__ == "__main__":
    unittest.main()
