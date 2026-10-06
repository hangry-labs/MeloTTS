import unittest
from unittest.mock import patch

import numpy as np

from melo.audio import (
    apply_audio_effects,
    atempo_filters,
    audio_effects_enabled,
    build_audio_effect_filters,
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


if __name__ == "__main__":
    unittest.main()
