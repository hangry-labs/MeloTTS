import os
import sys
import types
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import soundfile as sf
from fastapi.responses import Response
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
from melo.openai_compat import openai_speed_controls  # noqa: E402


class FakeModel:
    def __init__(self, speakers):
        data = SimpleNamespace(spk2id={speaker: index for index, speaker in enumerate(speakers)})
        data.sampling_rate = 22050
        self.hps = SimpleNamespace(data=data)

    @staticmethod
    def tts_to_file(_text, _speaker_id, destination, **_kwargs):
        sf.write(destination, np.zeros(2205, dtype=np.float32), 22050, format="WAV")

    @staticmethod
    def iter_audio_segments(_text, _speaker_id, **_kwargs):
        yield np.zeros(512, dtype=np.float32)
        yield np.full(512, 0.1, dtype=np.float32)


class OpenAICompatibilityApiTests(unittest.TestCase):
    def setUp(self):
        self.previous_models = dict(app_module.models)
        app_module.models.clear()
        app_module.models.update(
            {
                "EN": FakeModel(["EN-US", "EN-BR"]),
                "EN_V2": FakeModel(["EN-US", "EN-BR", "EN-AU"]),
                "EN_NEWEST": FakeModel(["EN-Newest"]),
                "ES": FakeModel(["ES"]),
            }
        )
        self.client = TestClient(app_module.api)

    def tearDown(self):
        self.client.close()
        app_module.models.clear()
        app_module.models.update(self.previous_models)

    def test_health_routes_report_ready(self):
        for path in ("/health", "/health/live", "/health/ready"):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["status"], "ok")

    def test_models_list_exposes_generic_and_language_specific_models(self):
        response = self.client.get("/v1/models")
        model = self.client.get("/v1/models/melotts-en-newest")

        self.assertEqual(response.status_code, 200)
        model_ids = [item["id"] for item in response.json()["data"]]
        self.assertEqual(model_ids[0], "melotts")
        self.assertIn("melotts-en-v2", model_ids)
        self.assertEqual(model.json()["id"], "melotts-en-newest")

    def test_voice_discovery_returns_objects_and_supports_model_filter(self):
        all_voices = self.client.get("/v1/audio/voices")
        spanish = self.client.get("/v1/audio/voices", params={"model": "melotts-es"})

        self.assertEqual(all_voices.status_code, 200)
        self.assertIn(
            {"id": "EN-Newest", "name": "EN-Newest", "language": "EN_NEWEST", "model": "melotts-en-newest"},
            all_voices.json()["voices"],
        )
        self.assertEqual(
            spanish.json()["voices"],
            [{"id": "ES", "name": "ES", "language": "ES", "model": "melotts-es"}],
        )

    def test_default_mp3_uses_sentence_streaming_and_best_matching_model(self):
        response = Response(content=b"audio", media_type="audio/mpeg")
        with patch(
            "melo.app.stream_tts_audio_segments", return_value=response
        ) as stream_response:
            result = self.client.post(
                "/v1/audio/speech",
                json={"model": "melotts", "input": "Test.", "voice": "EN-BR"},
            )

        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.content, b"audio")
        self.assertEqual(result.headers["x-melotts-model"], "melotts-en-v2")
        payload = stream_response.call_args.args[0]
        self.assertEqual(payload.language, "EN_V2")
        self.assertEqual(payload.stream_format, "mp3")

    def test_pcm_response_streams_sentence_chunks(self):
        response = self.client.post(
            "/v1/audio/speech",
            json={
                "model": "melotts-en-newest",
                "input": "First sentence. Second sentence.",
                "voice": "EN-Newest",
                "response_format": "pcm",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["x-melotts-stream-format"], "pcm_s16le")
        self.assertEqual(response.headers["x-melotts-stream-granularity"], "sentence")
        self.assertEqual(len(response.content), 2048)

    def test_wav_response_uses_complete_file_generation(self):
        response = Response(content=b"wave", media_type="audio/wav")
        with patch("melo.app.stream_tts_audio", return_value=response) as audio_response:
            result = self.client.post(
                "/v1/audio/speech",
                json={
                    "model": "melotts-es",
                    "input": "Hola.",
                    "voice": "ES",
                    "response_format": "wav",
                },
            )

        self.assertEqual(result.status_code, 200)
        payload = audio_response.call_args.args[0]
        self.assertEqual(payload.language, "ES")
        self.assertEqual(payload.output_format, "wav")

    def test_opus_and_aac_use_complete_file_generation(self):
        for response_format, media_type in (("opus", "audio/ogg"), ("aac", "audio/aac")):
            with self.subTest(response_format=response_format):
                response = Response(content=b"audio", media_type=media_type)
                with patch("melo.app.stream_tts_audio", return_value=response) as audio_response:
                    result = self.client.post(
                        "/v1/audio/speech",
                        json={
                            "model": "melotts-es",
                            "input": "Hola.",
                            "voice": "ES",
                            "response_format": response_format,
                        },
                    )

                self.assertEqual(result.status_code, 200)
                self.assertEqual(audio_response.call_args.args[0].output_format, response_format)

    def test_openai_speed_range_maps_to_native_and_tempo_controls(self):
        self.assertEqual(openai_speed_controls(0.25), (0.5, 0.5))
        self.assertEqual(openai_speed_controls(1.25), (1.25, 1.0))
        self.assertEqual(openai_speed_controls(4.0), (2.0, 2.0))

    def test_openai_validation_and_semantic_errors_use_error_envelope(self):
        cases = (
            ({"model": "melotts", "voice": "EN-Newest"}, "input"),
            (
                {
                    "model": "melotts",
                    "input": "Test.",
                    "voice": "EN-Newest",
                    "instructions": "Sound cheerful.",
                },
                "instructions",
            ),
            (
                {
                    "model": "melotts",
                    "input": "Test.",
                    "voice": "EN-Newest",
                    "response_format": "ogg",
                },
                "response_format",
            ),
        )
        for payload, expected_param in cases:
            with self.subTest(param=expected_param):
                response = self.client.post("/v1/audio/speech", json=payload)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.json()["error"]["param"], expected_param)

    def test_unknown_v1_routes_and_models_use_openai_errors(self):
        route = self.client.get("/v1/not-a-route")
        model = self.client.get("/v1/models/not-a-model")

        self.assertEqual(route.status_code, 404)
        self.assertIn("error", route.json())
        self.assertEqual(model.status_code, 400)
        self.assertEqual(model.json()["error"]["code"], "model_not_found")

    def test_optional_bearer_authentication(self):
        with patch.dict(os.environ, {"MELOTTS_API_KEY": "secret"}):
            missing = self.client.get("/v1/models")
            valid = self.client.get(
                "/v1/models", headers={"Authorization": "Bearer secret"}
            )

        self.assertEqual(missing.status_code, 401)
        self.assertEqual(missing.json()["error"]["type"], "authentication_error")
        self.assertEqual(missing.headers["www-authenticate"], "Bearer")
        self.assertEqual(valid.status_code, 200)


if __name__ == "__main__":
    unittest.main()
