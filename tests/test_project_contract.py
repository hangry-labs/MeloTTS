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

    def test_ssml_examples_page_has_generated_audio(self):
        examples = REPO_ROOT / "examples"
        page = (examples / "ssml.html").read_text(encoding="utf-8")
        expected_audio = {
            "melotts-ssml-studio-dialogue.mp3",
            "melotts-ssml-accent-roundtable.mp3",
            "melotts-ssml-multilingual-cafe.mp3",
            "melotts-ssml-east-asia.mp3",
            "melotts-ssml-directed-delivery.mp3",
        }

        self.assertTrue((examples / "ssml.css").is_file())
        self.assertTrue((examples / "ssml.js").is_file())
        for filename in expected_audio:
            self.assertIn(filename, page)
            path = examples / filename
            self.assertTrue(path.is_file(), filename)
            self.assertGreater(path.stat().st_size, 10_000, filename)

    def test_ssml_example_generator_is_windows_powershell_safe(self):
        script = (REPO_ROOT / "scripts" / "generate-ssml-examples.ps1").read_bytes()

        self.assertTrue(script.isascii())
        self.assertIn(b"Expand-UnicodeEscapes", script)

    def test_korean_frontend_has_build_and_runtime_dependencies(self):
        requirements = (REPO_ROOT / "requirements.in").read_text(encoding="utf-8")
        dockerfile = (REPO_ROOT / "Dockerfile").read_text(encoding="utf-8")

        self.assertIn("python-mecab-ko", requirements)
        self.assertIn("libmecab-dev", dockerfile)
        self.assertIn("libmecab2", dockerfile)

    def test_unidic_build_input_is_pinned_and_cache_aware(self):
        dockerfile = (REPO_ROOT / "Dockerfile").read_text(encoding="utf-8")
        workflow = (REPO_ROOT / ".github/workflows/docker-build.yml").read_text(
            encoding="utf-8"
        )
        checksum = "638718c4c63625ab300de4c92c67925d54c0e9e3830009eaa992f29819d59c43"

        self.assertIn("scripts/install_unidic.py", dockerfile)
        self.assertIn(checksum, dockerfile)
        self.assertIn("actions/cache@v4", workflow)
        self.assertIn("UNIDIC_SHA256", workflow)


if __name__ == "__main__":
    unittest.main()
