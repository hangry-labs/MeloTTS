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
        self.assertEqual(force_include["LICENSE"], "LICENSE")
        self.assertEqual(force_include["LICENSES"], "LICENSES")
        self.assertEqual(
            force_include["THIRD_PARTY_NOTICES.md"], "THIRD_PARTY_NOTICES.md"
        )
        self.assertFalse((REPO_ROOT / "setup.py").exists())

    def test_license_and_notices_are_declared(self):
        project = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        license_text = (REPO_ROOT / "LICENSE").read_text(encoding="utf-8")
        notices = (REPO_ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")

        self.assertEqual(project["project"]["license"], "AGPL-3.0-only")
        self.assertIn("GNU AFFERO GENERAL PUBLIC LICENSE", license_text)
        self.assertIn("Bert-VITS2", notices)
        self.assertIn("Copyright (c) 2024 MyShell.ai", notices)
        self.assertTrue((REPO_ROOT / "LICENSES" / "MIT-MeloTTS.txt").is_file())
        self.assertTrue((REPO_ROOT / "LICENSES" / "Apache-2.0.txt").is_file())

    def test_model_downloads_are_pinned_to_reviewed_revisions(self):
        from melo.model_registry import BERT_MODEL_REVISIONS, TTS_MODEL_REVISIONS

        self.assertEqual(
            set(TTS_MODEL_REVISIONS),
            {"EN", "EN_V2", "EN_NEWEST", "ES", "FR", "ZH", "JP", "KR"},
        )
        for revision in [*TTS_MODEL_REVISIONS.values(), *BERT_MODEL_REVISIONS.values()]:
            self.assertRegex(revision, r"^[0-9a-f]{40}$")

    def test_optional_spanish_and_korean_models_are_not_baked(self):
        from melo.init_downloads import FULL_BERT_MODELS, FULL_LANGUAGES
        from melo.optional_models import OPTIONAL_LANGUAGE_CODES

        self.assertTrue(set(OPTIONAL_LANGUAGE_CODES).isdisjoint(FULL_LANGUAGES))
        self.assertNotIn("dccuchile/bert-base-spanish-wwm-uncased", FULL_BERT_MODELS)
        self.assertNotIn("kykim/bert-kor-base", FULL_BERT_MODELS)

        dockerfile = (REPO_ROOT / "Dockerfile").read_text(encoding="utf-8")
        taskfile = (REPO_ROOT / "Taskfile.yml").read_text(encoding="utf-8")
        self.assertIn("HF_HOME=/app/persistent/models/huggingface", dockerfile)
        self.assertIn('DEFAULT_TTS_LANGUAGES="EN,EN_V2,EN_NEWEST,FR,ZH,JP"', dockerfile)
        self.assertIn(
            "melo/api.py melo/attentions.py melo/audio.py melo/commons.py", dockerfile
        )
        self.assertIn("melotts_data", taskfile)
        self.assertIn(":/app/persistent", taskfile)

    def test_repository_assets_are_webp_only(self):
        assets = [path for path in (REPO_ROOT / "assets").iterdir() if path.is_file()]

        self.assertTrue(assets)
        self.assertEqual({path.suffix.lower() for path in assets}, {".webp"})

    def test_public_pages_use_current_brand_and_local_styles(self):
        public_files = [
            REPO_ROOT / "README.md",
            REPO_ROOT / "404.html",
            REPO_ROOT / "docs" / "dockerhub.md",
            REPO_ROOT / "examples" / "index.html",
            REPO_ROOT / "examples" / "ssml.html",
            REPO_ROOT / "melo" / "standalone_ui" / "static" / "index.html",
        ]
        content = "\n".join(path.read_text(encoding="utf-8") for path in public_files)

        self.assertNotIn("Melo T T S", content)
        self.assertNotIn("nuggies.website", content)
        self.assertNotIn("cdn.tailwindcss.com", content)
        self.assertNotIn("tailwind.css", content)
        self.assertNotIn("Tailwind CSS", content)
        self.assertIn("https://hangrylabs.app/", content)
        self.assertFalse((REPO_ROOT / "examples" / "tailwind.css").exists())

    def test_readme_uses_immutable_release_images_and_rolling_snapshot_images(self):
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        docker_commands = [
            line for line in readme.splitlines() if line.startswith("docker run ")
        ]

        self.assertIn("hangrylabs/melotts:latest", readme)
        self.assertIn("hangrylabs/melotts:latest_en", readme)
        self.assertRegex(
            readme,
            r"hangrylabs/melotts:v0\.1\.0@sha256:[0-9a-f]{64}",
        )
        self.assertRegex(
            readme,
            r"hangrylabs/melotts:v0\.1\.0_en@sha256:[0-9a-f]{64}",
        )
        self.assertNotRegex(
            readme,
            r"hangrylabs/melotts:v0\.0\.[0-9](?:_en)?(?:\s|$)",
        )
        self.assertTrue(docker_commands)
        self.assertTrue(all("\\" not in command for command in docker_commands))

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
