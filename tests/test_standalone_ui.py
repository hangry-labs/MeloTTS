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
        self.assertIn('src="/assets/melotts_logo_horizontal.webp"', index.text)
        self.assertIn('href="/assets/melotts_favicon.webp"', index.text)
        self.assertIn('src="/assets/hangrylabs_logo.webp"', index.text)
        self.assertNotIn("gradio", index.text.lower())
        self.assertEqual(script.status_code, 200)
        self.assertIn("/tts/generate", script.text)
        self.assertIn("/tts/stream", script.text)
        self.assertIn("`/tts/${action}`", script.text)
        self.assertIn("modelActionButton('Load', 'load'", script.text)
        self.assertIn("modelActionButton('Keep only', 'purge'", script.text)
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

    def test_english_catalog_covers_static_translation_keys(self) -> None:
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
