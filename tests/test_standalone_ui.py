from __future__ import annotations

import json
import re
import time
import unittest
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from melo.standalone_ui.gpu import GpuMonitor, read_gpu_stats
from melo.standalone_ui.server import LOCALES_DIR, create_app


class StandaloneUiTests(unittest.TestCase):
    @staticmethod
    def backend_app() -> FastAPI:
        backend = FastAPI()

        @backend.get("/tts/ping")
        async def ping() -> dict[str, str]:
            return {"msg": "pong"}

        return backend

    def test_workspace_assets_and_api_are_available(self) -> None:
        gpu_payload = {
            "gpus": [],
            "history": {},
            "sample_interval_seconds": 1,
            "idle_timeout_seconds": 60,
        }
        with patch(
            "melo.standalone_ui.server.GPU_MONITOR.request_snapshot",
            return_value=gpu_payload,
        ):
            with TestClient(create_app(api_app=self.backend_app())) as client:
                index = client.get("/")
                script = client.get("/static/app.js")
                translations = client.get("/static/i18n.js")
                locale_manifest = client.get("/static/locales/manifest.json")
                stylesheet = client.get("/static/styles.css")
                waveform = client.get("/static/vendor/wavesurfer/wavesurfer.esm.js")
                product_logo = client.get("/assets/melotts_logo_horizontal.webp")
                favicon = client.get("/assets/melotts_favicon.webp")
                labs_logo = client.get("/assets/hangrylabs_logo.webp")
                gpu = client.get("/system/gpu")
                api = client.get("/tts/ping")

        self.assertEqual(index.status_code, 200)
        self.assertIn("Melo TTS", index.text)
        self.assertIn('<span class="runtime-version-label">UI v', index.text)
        self.assertNotIn("UI vv", index.text)
        self.assertIn('data-tab="generate"', index.text)
        self.assertIn('data-tab="stream"', index.text)
        self.assertIn('data-tab="api"', index.text)
        self.assertIn('data-tab="system"', index.text)
        self.assertIn('id="sdp-ratio"', index.text)
        self.assertIn('id="noise-scale"', index.text)
        self.assertIn('id="noise-scale-w"', index.text)
        self.assertIn('id="pitch"', index.text)
        self.assertIn('id="tempo"', index.text)
        self.assertIn('id="volume"', index.text)
        self.assertIn('id="normalize"', index.text)
        self.assertIn('id="ssml-mode-button"', index.text)
        self.assertIn('id="ssml-help-dialog"', index.text)
        self.assertIn('id="optional-model-groups"', index.text)
        self.assertIn('id="optional-model-dialog"', index.text)
        self.assertIn('src="/assets/melotts_logo_horizontal.webp"', index.text)
        self.assertIn('href="/assets/melotts_favicon.webp"', index.text)
        self.assertIn('src="/assets/hangrylabs_logo.webp"', index.text)
        self.assertIn('<span data-i18n="nav.source">Source</span>', index.text)
        self.assertIn('data-i18n-title="nav.sourceTitle"', index.text)
        self.assertIn("https://hangry-labs.github.io/MeloTTS/examples/?lang=en", index.text)
        self.assertIn('href="https://hangrylabs.app/software/melotts"', index.text)
        self.assertIn('id="ui-locale"', index.text)
        self.assertIn('"locale":"en"', index.text)
        self.assertIn('"messages":{"app.title":"Melo TTS"', index.text)
        self.assertNotIn("gradio", index.text.lower())
        self.assertEqual(script.status_code, 200)
        self.assertEqual(translations.status_code, 200)
        self.assertIn("localStorage.setItem(bootstrap.storageKey", translations.text)
        self.assertEqual(locale_manifest.status_code, 200)
        self.assertEqual(locale_manifest.json()["defaultLocale"], "en")
        self.assertIn("/tts/generate", script.text)
        self.assertIn("/tts/stream", script.text)
        self.assertIn("pitch_semitones: Number($('#pitch').value)", script.text)
        self.assertIn("input_type: state.inputType", script.text)
        self.assertIn("function setInputType(inputType)", script.text)
        self.assertIn("`/tts/${action}`", script.text)
        self.assertIn("modelActionButton(t('residency.load'), 'load'", script.text)
        self.assertIn("modelActionButton(t('residency.keepOnly'), 'purge'", script.text)
        self.assertIn("/system/settings/models", script.text)
        self.assertIn("accept_upstream_terms: true", script.text)
        self.assertIn("function addGpuChartGrid(", script.text)
        self.assertIn("function attachGpuChartHover(", script.text)
        self.assertIn("gpu-chart-area", script.text)
        self.assertIn("gpu-live-details", script.text)
        self.assertIn("setAttribute('aria-label', t('gpu.historyAria'", script.text)
        self.assertEqual(stylesheet.status_code, 200)
        self.assertIn(".product-fallback", stylesheet.text)
        self.assertIn(".gpu-hover-tooltip", stylesheet.text)
        self.assertIn(".gpu-live-details", stylesheet.text)
        self.assertEqual(waveform.status_code, 200)
        self.assertEqual(product_logo.status_code, 200)
        self.assertEqual(product_logo.headers["content-type"], "image/webp")
        self.assertEqual(favicon.status_code, 200)
        self.assertEqual(labs_logo.status_code, 200)
        self.assertEqual(labs_logo.headers["content-type"], "image/webp")
        self.assertEqual(gpu.status_code, 200)
        self.assertIn("gpus", gpu.json())
        self.assertIn("history", gpu.json())
        self.assertEqual(gpu.headers["cache-control"], "no-store")
        self.assertEqual(api.json(), {"msg": "pong"})

    def test_unknown_paths_return_not_found(self) -> None:
        with TestClient(create_app(api_app=self.backend_app())) as client:
            self.assertEqual(client.get("/not-allowed").status_code, 404)

    def test_supported_locale_routes_and_catalogs_are_complete(self) -> None:
        expected_locales = ("en", "es", "fr", "ja", "zh", "ko")
        product_urls = {
            "en": "https://hangrylabs.app/software/melotts",
            "es": "https://hangrylabs.app/es/software/melotts",
            "fr": "https://hangrylabs.app/software/melotts",
            "ja": "https://hangrylabs.app/ja/software/melotts",
            "zh": "https://hangrylabs.app/zh/software/melotts",
            "ko": "https://hangrylabs.app/software/melotts",
        }
        english = json.loads((LOCALES_DIR / "en.json").read_text(encoding="utf-8"))
        static_dir = LOCALES_DIR.parent
        referenced_keys = set(
            re.findall(
                r'data-i18n(?:-[a-z-]+)?="([^"]+)"',
                (static_dir / "index.html").read_text(encoding="utf-8"),
            )
        )
        for script_name in ("app.js", "audio-editor.js", "i18n.js"):
            referenced_keys.update(
                re.findall(
                    r"\bt\(['\"]([^'\"]+)['\"]",
                    (static_dir / script_name).read_text(encoding="utf-8"),
                )
            )

        self.assertFalse(referenced_keys - set(english))
        for dynamic_key in (
            "languages.EN",
            "languages.EN_V2",
            "languages.EN_NEWEST",
            "languages.FR",
            "languages.ZH",
            "languages.JP",
            "languages.ES",
            "languages.KR",
            "presets.balanced",
            "presets.expressive",
            "optional.warning.ES",
            "optional.warning.KR",
        ):
            self.assertIn(dynamic_key, english)

        with TestClient(create_app(api_app=self.backend_app())) as client:
            for locale in expected_locales:
                response = client.get(f"/{locale}")
                self.assertEqual(response.status_code, 200, locale)
                self.assertIn(f'<html lang="{locale}" dir="ltr">', response.text)
                self.assertIn(f'"locale":"{locale}"', response.text)
                self.assertIn(
                    f"https://hangry-labs.github.io/MeloTTS/examples/?lang={locale}",
                    response.text,
                )
                self.assertIn(f'href="{product_urls[locale]}"', response.text)

                catalog_response = client.get(f"/static/locales/{locale}.json")
                self.assertEqual(catalog_response.status_code, 200, locale)
                catalog = catalog_response.json()
                self.assertEqual(set(catalog), set(english), locale)
                self.assertTrue(
                    all(isinstance(value, str) and value for value in catalog.values()),
                    locale,
                )

            self.assertEqual(client.get("/de").status_code, 404)

    def test_examples_page_supports_localized_language_filters(self) -> None:
        root = LOCALES_DIR.parents[3]
        page = (root / "examples" / "index.html").read_text(encoding="utf-8")
        player = (root / "examples" / "player.js").read_text(encoding="utf-8")

        for locale, label in (
            ("en", "English"),
            ("es", "Español"),
            ("fr", "Français"),
            ("ja", "日本語"),
            ("zh", "简体中文"),
            ("ko", "한국어"),
        ):
            self.assertIn(f'data-language-value="{locale}"', page)
            self.assertIn(label, page)
        self.assertIn('new URLSearchParams(window.location.search).get("lang")', player)
        self.assertIn('setLanguageFilter(PAGE_LANGUAGES.has(requestedLanguage)', player)
        self.assertIn('title: "Hangry Labs Melo TTS 음성 예제"', player)
        self.assertIn('headline: "声音示例"', player)
        self.assertIn('data-product-link', page)
        self.assertIn('es: "https://hangrylabs.app/es/software/melotts"', player)
        self.assertIn('zh: "https://hangrylabs.app/zh/software/melotts"', player)
        self.assertNotIn("cdn.tailwindcss.com", page)

    def test_public_documentation_language_navigation_is_utf8(self) -> None:
        root = LOCALES_DIR.parents[3]
        documents = [
            root / "README.md",
            root / "README.es.md",
            root / "README.nb.md",
            root / "README.pl.md",
            root / "README.ja.md",
            root / "README.zh.md",
            root / "docs" / "dockerhub.md",
        ]
        labels = ("English", "Norsk bokmål", "Polski", "日本語", "简体中文", "Español")
        for document in documents:
            contents = document.read_text(encoding="utf-8")
            for label in labels:
                self.assertIn(label, contents, document.name)
            for marker in ("Â·", "EspaÃ±ol", "FranÃ§ais", "æ—¥æœ¬èªž", "ÃƒÂ", "\ufffd"):
                self.assertNotIn(marker, contents, document.name)
            self.assertRegex(
                contents,
                r"https://hangrylabs\.app/(?:es/|ja/|nb/|pl/|zh/)?software/melotts",
            )

    def test_development_assets_disable_browser_caching(self) -> None:
        with patch.dict("os.environ", {"MELOTTS_UI_DEV": "1"}):
            with TestClient(create_app(api_app=self.backend_app())) as client:
                index = client.get("/")
                stylesheet = client.get("/static/styles.css")
                favicon = client.get("/assets/melotts_favicon.webp")

        self.assertEqual(index.headers["cache-control"], "no-store")
        self.assertEqual(stylesheet.headers["cache-control"], "no-store")
        self.assertEqual(favicon.headers["cache-control"], "no-store")

    @patch("melo.standalone_ui.gpu.subprocess.run")
    def test_gpu_monitor_parses_nvidia_smi(self, run) -> None:
        run.return_value.returncode = 0
        run.return_value.stdout = (
            "0, NVIDIA RTX Test, 37, 12, 4096, 16384, 52, 30, 61.5, 300, "
            "2400, 3000, 13000, 14000, P2, 5, 16\n"
        )

        stats = read_gpu_stats()

        self.assertEqual(stats[0]["utilization"], 37)
        self.assertEqual(stats[0]["memory_total"], 16384)
        self.assertEqual(stats[0]["name"], "NVIDIA RTX Test")
        self.assertEqual(stats[0]["temperature"], 52)
        self.assertEqual(stats[0]["power"], 61.5)
        self.assertEqual(stats[0]["fan_speed"], 30)
        self.assertEqual(stats[0]["graphics_clock"], 2400)
        self.assertEqual(stats[0]["performance_state"], "P2")

    @patch("melo.standalone_ui.gpu.subprocess.run")
    def test_gpu_monitor_keeps_optional_missing_values(self, run) -> None:
        run.return_value.returncode = 0
        run.return_value.stdout = (
            "0, NVIDIA Compute GPU, 75, N/A, 1024, 8192, 48, [N/A], 125, 250, "
            "1800, N/A, N/A, N/A, P0, 4, 16\n"
        )

        stats = read_gpu_stats()

        self.assertEqual(len(stats), 1)
        self.assertIsNone(stats[0]["fan_speed"])
        self.assertIsNone(stats[0]["memory_utilization"])
        self.assertEqual(stats[0]["power"], 125.0)

    def test_gpu_monitor_samples_until_idle_timeout(self) -> None:
        calls = 0

        def reader():
            nonlocal calls
            calls += 1
            return [{"index": 0, "name": "Test GPU", "utilization": calls}]

        monitor = GpuMonitor(reader, sample_interval=0.01, idle_timeout=0.2, history_seconds=1)
        try:
            first = monitor.request_snapshot()
            self.assertEqual(first["gpus"][0]["utilization"], 1)

            deadline = time.monotonic() + 0.2
            while calls < 3 and time.monotonic() < deadline:
                time.sleep(0.01)
            self.assertGreaterEqual(calls, 3)

            time.sleep(0.22)
            stopped_at = calls
            time.sleep(0.05)
            self.assertEqual(calls, stopped_at)
            self.assertGreaterEqual(len(monitor.request_snapshot()["history"]["0"]), 3)
        finally:
            monitor.close()


if __name__ == "__main__":
    unittest.main()
