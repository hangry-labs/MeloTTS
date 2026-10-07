import unittest

from melo.text.korean_utils.normalization import (
    normalize_compatibility_jamo,
    normalize_oversized_numbers,
)


class KoreanNormalizationTests(unittest.TestCase):
    def test_standalone_consonants_are_verbalized(self):
        self.assertEqual(
            normalize_compatibility_jamo("ㄱㄴㄷㄹㅁㅂㅅ"),
            "기역, 니은, 디귿, 리을, 미음, 비읍, 시옷",
        )

    def test_standalone_vowels_are_verbalized(self):
        self.assertEqual(
            normalize_compatibility_jamo("ㅏㅑㅓㅕㅗㅛ"),
            "아, 야, 어, 여, 오, 요",
        )

    def test_jamo_next_to_korean_text_keeps_the_sentence_attached(self):
        self.assertEqual(
            normalize_compatibility_jamo("자음 ㄱ입니다."),
            "자음 기역입니다.",
        )

    def test_supported_cardinal_number_is_preserved_for_g2p(self):
        self.assertEqual(
            normalize_oversized_numbers("1234567890123456원"),
            "1234567890123456원",
        )

    def test_oversized_number_falls_back_to_digit_names(self):
        self.assertEqual(
            normalize_oversized_numbers("12345678901234567원"),
            "일이삼사오육칠팔구영일이삼사오육칠원",
        )

    def test_commas_do_not_count_toward_the_cardinal_limit(self):
        self.assertEqual(
            normalize_oversized_numbers("12,345,678,901,234,567개"),
            "일이삼사오육칠팔구영일이삼사오육칠개",
        )


if __name__ == "__main__":
    unittest.main()
