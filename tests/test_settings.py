import json
import tempfile
import unittest
from pathlib import Path

from melo.settings import RuntimeSettingsStore


class RuntimeSettingsStoreTests(unittest.TestCase):
    def test_optional_languages_are_validated_and_written_atomically(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "app" / "settings.json"
            store = RuntimeSettingsStore(path)

            self.assertEqual(store.optional_languages(("ES", "KR")), [])
            self.assertEqual(store.set_optional_languages(["KR"], ("ES", "KR")), ["KR"])
            self.assertEqual(store.optional_languages(("ES", "KR")), ["KR"])
            self.assertEqual(json.loads(path.read_text())["optional_languages"], ["KR"])

            with self.assertRaisesRegex(ValueError, "Unsupported optional languages"):
                store.set_optional_languages(["XX"], ("ES", "KR"))


if __name__ == "__main__":
    unittest.main()
