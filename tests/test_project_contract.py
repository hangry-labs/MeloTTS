import tomllib
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


class ProjectContractTests(unittest.TestCase):
    def test_display_and_package_versions_match(self):
        display_version = (REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip()
        project = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        expected = display_version.removeprefix("v").replace("-SNAPSHOT", ".dev0")

        self.assertEqual(project["project"]["version"], expected)

    def test_wheel_contract_includes_runtime_root_files(self):
        project = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        force_include = project["tool"]["hatch"]["build"]["targets"]["wheel"][
            "force-include"
        ]

        self.assertEqual(force_include["assets"], "assets")
        self.assertEqual(force_include["VERSION"], "VERSION")
        self.assertFalse((REPO_ROOT / "setup.py").exists())

    def test_repository_assets_are_webp_only(self):
        assets = [path for path in (REPO_ROOT / "assets").iterdir() if path.is_file()]

        self.assertTrue(assets)
        self.assertEqual({path.suffix.lower() for path in assets}, {".webp"})


if __name__ == "__main__":
    unittest.main()
