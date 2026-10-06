import importlib
import sys
import types
import unittest
from unittest.mock import patch


class ChineseNumberNormalizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cn2an_stub = types.ModuleType("cn2an")

        def fake_an2cn(value, mode=None):
            direct = {"2018": "二零一八", "2026": "二零二六"}
            cardinal = {
                "3.14": "三点一四",
                "5": "五",
                "18": "十八",
                "2018": "二千零一十八",
            }
            return direct[value] if mode == "direct" else cardinal[value]

        cn2an_stub.an2cn = fake_an2cn
        with patch.dict(sys.modules, {"cn2an": cn2an_stub}):
            module = importlib.import_module("melo.text.chinese_numbers")
        cls.normalize = staticmethod(module.normalize_chinese_numbers)

    def test_four_digit_year_uses_direct_digit_reading(self):
        self.assertEqual(self.normalize("2018年"), "二零一八年")
        self.assertEqual(
            self.normalize("2018年5月18日"),
            "二零一八年五月十八日",
        )

    def test_non_year_numbers_keep_cardinal_conversion(self):
        self.assertEqual(
            self.normalize("共有2018个,值为3.14"),
            "共有二千零一十八个,值为三点一四",
        )


if __name__ == "__main__":
    unittest.main()
