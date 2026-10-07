import importlib
import sys
import types
import unittest
from unittest.mock import patch


class ToneSandhiMergeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        jieba_stub = types.ModuleType("jieba")
        jieba_stub.cut_for_search = lambda word: [word]

        pypinyin_stub = types.ModuleType("pypinyin")
        pypinyin_stub.lazy_pinyin = lambda *args, **kwargs: []
        pypinyin_stub.Style = types.SimpleNamespace(FINALS_TONE3="finals-tone3")

        with patch.dict(
            sys.modules,
            {"jieba": jieba_stub, "pypinyin": pypinyin_stub},
        ):
            module = importlib.import_module("melo.text.tone_sandhi")
        cls.sandhi = module.ToneSandhi()

    def test_reduplicated_yi_merge_skips_differently_tagged_right_verb(self):
        segment = [
            ("又", "d"),
            ("指", "v"),
            ("一", "m"),
            ("指", "n"),
            ("自己", "r"),
        ]
        self.assertEqual(
            self.sandhi._merge_yi(segment),
            [["又", "d"], ["指一指", "v"], ["自己", "r"]],
        )

    def test_standalone_yi_still_merges_with_following_word(self):
        self.assertEqual(
            self.sandhi._merge_yi([("看", "v"), ("一", "m"), ("下", "q")]),
            [["看", "v"], ["一下", "m"]],
        )


if __name__ == "__main__":
    unittest.main()
