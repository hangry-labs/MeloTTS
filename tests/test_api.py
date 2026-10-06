import io
import os
import sys
import types
import unittest
from types import SimpleNamespace

import numpy as np
import soundfile as sf
from fastapi.testclient import TestClient

os.environ["MELOTTS_EAGER_LOAD"] = "0"

torch_stub = types.ModuleType("torch")
torch_stub.cuda = SimpleNamespace(
    is_available=lambda: False,
    device_count=lambda: 0,
    empty_cache=lambda: None,
)
torch_stub.backends = SimpleNamespace(mps=SimpleNamespace(is_available=lambda: False))
sys.modules.setdefault("torch", torch_stub)

api_stub = types.ModuleType("melo.api")
api_stub.TTS = type("TTS", (), {})
sys.modules.setdefault("melo.api", api_stub)

from melo import app as app_module  # noqa: E402


class FakeModel:
    last_tts_kwargs = None

    def __init__(self):
        data = SimpleNamespace(spk2id={"EN-BR": 0}, sampling_rate=22050)
        self.hps = SimpleNamespace(data=data)

    @staticmethod
    def tts_to_file(_text, _speaker_id, destination, **_kwargs):
        FakeModel.last_tts_kwargs = _kwargs
        sf.write(destination, np.zeros(2205, dtype=np.float32), 22050, format="WAV")

    @staticmethod
    def iter_audio_segments(_text, _speaker_id, **_kwargs):
        yield np.zeros(512, dtype=np.float32)
        yield np.full(512, 0.1, dtype=np.float32)


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.previous_models = dict(app_module.models)
        app_module.models.clear()
        app_module.models["EN"] = FakeModel()
        FakeModel.last_tts_kwargs = None
        self.client = TestClient(app_module.api)

    def tearDown(self):
        self.client.close()
        app_module.models.clear()
        app_module.models.update(self.previous_models)

    @staticmethod
    def request_body(**overrides):
        body = {
            "text": "A private sentence that must not appear in logs.",
            "language": "EN",
            "speaker_id": "EN-BR",
        }
        body.update(overrides)
        return body

    def test_status_reports_configured_and_loaded_languages(self):
        response = self.client.get("/tts/status")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["version"], app_module.VERSION)
        self.assertIn("EN", payload["configured_languages"])
        self.assertEqual(payload["loaded_languages"], ["EN"])

    def test_generate_defaults_to_backward_compatible_wav(self):
        secret = self.request_body()["text"]
        with self.assertLogs("TTSApp", level="INFO") as captured:
            response = self.client.post("/tts/generate", json=self.request_body())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "audio/wav")
        self.assertEqual(response.headers["x-melotts-language"], "EN")
        self.assertNotIn(secret, "\n".join(captured.output))
        self.assertTrue(FakeModel.last_tts_kwargs["quiet"])
        audio, sample_rate = sf.read(io.BytesIO(response.content))
        self.assertEqual(sample_rate, 22050)
        self.assertEqual(len(audio), 2205)

    def test_generate_supports_flac_alias_and_rejects_unknown_speaker(self):
        response = self.client.post(
            "/tts/generate",
            json=self.request_body(format=".flac"),
        )
        invalid = self.client.post(
            "/tts/generate",
            json=self.request_body(speaker_id="missing"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "audio/flac")
        self.assertEqual(response.headers["x-melotts-format"], "flac")
        self.assertEqual(invalid.status_code, 400)
        self.assertEqual(invalid.json()["detail"], "Invalid speaker_id 'missing'")

    def test_validation_logs_do_not_include_request_text(self):
        private_text = "do-not-log-this-validation-payload"
        with self.assertLogs("TTSApp", level="WARNING") as captured:
            response = self.client.post(
                "/tts/generate",
                json={"text": private_text, "language": "EN"},
            )

        self.assertEqual(response.status_code, 422)
        self.assertNotIn(private_text, "\n".join(captured.output))

    def test_stream_returns_sentence_level_pcm(self):
        response = self.client.post("/tts/stream", json=self.request_body())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["x-melotts-stream-format"], "pcm_s16le")
        self.assertEqual(response.headers["x-melotts-stream-granularity"], "sentence")
        self.assertEqual(len(response.content), 2048)

    def test_deprecated_route_remains_backward_compatible(self):
        response = self.client.post("/tts/convert/tts", json=self.request_body())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "audio/wav")


if __name__ == "__main__":
    unittest.main()
