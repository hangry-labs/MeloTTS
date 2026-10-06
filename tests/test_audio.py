import io
import shutil
import unittest
from unittest.mock import patch

import numpy as np
import soundfile as sf

from melo.audio import (
    apply_audio_effects,
    atempo_filters,
    audio_effects_enabled,
    build_audio_effect_filters,
    compact_ssml_speech_audio,
    encode_audio_bytes,
    encode_mp3_stream,
    get_supported_output_formats,
    trim_silent_audio_edges,
)


class AudioEffectsTests(unittest.TestCase):
    def test_neutral_controls_skip_processing(self):
        audio = np.array([0.0, 0.25, -0.25], dtype=np.float32)

        result = apply_audio_effects(audio, 22050)

        self.assertFalse(audio_effects_enabled())
        np.testing.assert_array_equal(result, audio)

    def test_filters_keep_pitch_and_tempo_independent(self):
        filters = build_audio_effect_filters(
            22050,
            pitch_semitones=12,
            tempo=1.25,
            volume=0.75,
            normalize=True,
        )

        self.assertEqual(filters[0:2], ["asetrate=44100", "aresample=22050"])
        self.assertIn("atempo=0.500000", filters)
        self.assertIn("atempo=1.250000", filters)
        self.assertIn("volume=0.750000", filters)
        self.assertEqual(filters[-1], "loudnorm=I=-16:TP=-1.5:LRA=11")

    def test_atempo_splits_values_outside_single_filter_range(self):
        self.assertEqual(atempo_filters(4), ["atempo=2.0", "atempo=2.000000"])
        self.assertEqual(atempo_filters(0.25), ["atempo=0.5", "atempo=0.500000"])

    def test_ssml_compaction_only_trims_requested_edges_and_adds_exact_handoff(self):
        sample_rate = 1000
        audio = np.concatenate(
            (
                np.zeros(100, dtype=np.float32),
                np.full(200, 0.5, dtype=np.float32),
                np.zeros(100, dtype=np.float32),
            )
        )

        leading_only = trim_silent_audio_edges(
            audio, sample_rate, leading=True, trailing=False
        )
        compacted = compact_ssml_speech_audio(
            audio,
            trim_leading=True,
            trim_trailing=True,
            append_implicit_pause=True,
            sample_rate=sample_rate,
        )

        self.assertEqual(len(leading_only), 300)
        self.assertEqual(len(compacted), 300)
        np.testing.assert_array_equal(compacted[:200], np.full(200, 0.5, dtype=np.float32))
        np.testing.assert_array_equal(compacted[200:], np.zeros(100, dtype=np.float32))

    def test_ssml_compaction_preserves_quiet_model_speech(self):
        sample_rate = 1000
        quiet_speech = np.linspace(-0.0005, 0.0005, 200, dtype=np.float32)
        audio = np.concatenate(
            (
                np.zeros(100, dtype=np.float32),
                quiet_speech,
                np.zeros(100, dtype=np.float32),
            )
        )

        compacted = compact_ssml_speech_audio(
            audio,
            trim_leading=True,
            trim_trailing=True,
            append_implicit_pause=False,
            sample_rate=sample_rate,
        )

        self.assertGreaterEqual(len(compacted), len(quiet_speech))
        self.assertGreater(float(np.max(np.abs(compacted))), 0.0004)

    @patch("melo.audio._run_ffmpeg")
    def test_effect_processing_returns_float_audio(self, run_ffmpeg):
        expected = np.array([0.1, -0.2], dtype="<f4")
        run_ffmpeg.return_value = expected.tobytes()

        result = apply_audio_effects(
            np.zeros(16, dtype=np.float32),
            22050,
            volume=0.8,
        )

        np.testing.assert_array_equal(result, expected)
        command = run_ffmpeg.call_args.args[0]
        self.assertIn("volume=0.800000", command)
        self.assertIn("f32le", command)

    @unittest.skipUnless(shutil.which("ffmpeg"), "ffmpeg is required for MP3 streaming")
    def test_mp3_stream_uses_one_continuous_encoder(self):
        sample_rate = 22050
        first = np.zeros(sample_rate // 10, dtype="<i2").tobytes()
        second = np.full(sample_rate // 10, 1000, dtype="<i2").tobytes()

        chunks = list(encode_mp3_stream(iter((first, second)), sample_rate, read_size=128))
        encoded = b"".join(chunks)
        audio, decoded_rate = sf.read(io.BytesIO(encoded))

        self.assertGreater(len(chunks), 1)
        self.assertNotIn(b"Xing", encoded)
        self.assertEqual(decoded_rate, sample_rate)
        self.assertGreater(len(audio), sample_rate // 10)

    @unittest.skipUnless(shutil.which("ffmpeg"), "ffmpeg is required for Opus and AAC")
    def test_ffmpeg_output_formats_are_available_and_encoded(self):
        audio = np.zeros(2205, dtype=np.float32)
        supported = get_supported_output_formats()

        self.assertIn("opus", supported)
        self.assertIn("aac", supported)
        opus = encode_audio_bytes(audio, 22050, "opus").getvalue()
        aac = encode_audio_bytes(audio, 22050, "aac").getvalue()
        self.assertTrue(opus.startswith(b"OggS"))
        self.assertTrue(aac.startswith((b"\xff\xf1", b"\xff\xf9")))


if __name__ == "__main__":
    unittest.main()
