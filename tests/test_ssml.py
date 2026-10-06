from __future__ import annotations

import unittest

from melo.ssml import (
    MAX_BREAK_MS,
    MAX_SSML_NESTING,
    SSMLValidationError,
    compile_ssml,
    parse_ssml,
)


class SsmlTests(unittest.TestCase):
    @staticmethod
    def resolve_language(value: str) -> str:
        aliases = {"en-US": "EN", "es-ES": "ES", "zh-CN": "ZH"}
        try:
            return aliases[value]
        except KeyError as error:
            raise ValueError(f"Unsupported language '{value}'.") from error

    @staticmethod
    def resolve_voice(voice: str) -> str:
        voices = {"EN-BR": "EN", "EN-Newest": "EN_NEWEST", "ES": "ES"}
        try:
            return voices[voice]
        except KeyError as error:
            raise ValueError(f"Voice '{voice}' is not loaded.") from error

    def compile(self, document: str, language: str = "EN", voice: str = "EN-BR"):
        return compile_ssml(
            document,
            language,
            default_voice=voice,
            resolve_language=self.resolve_language,
            resolve_voice_language=self.resolve_voice,
        )

    def parse(self, document: str, language: str = "EN", voice: str = "EN-BR"):
        return parse_ssml(
            document,
            language,
            default_voice=voice,
            resolve_language=self.resolve_language,
            resolve_voice_language=self.resolve_voice,
        )

    def test_supported_elements_compile_into_ordered_units(self):
        units = self.compile(
            """<speak version="1.0">
              Hello <sub alias="World Wide Web Consortium">W3C</sub>.
              <break time="500ms"/>
              Attempt <say-as interpret-as="ordinal">3</say-as> by
              <say-as interpret-as="characters">API</say-as>.
            </speak>"""
        )

        self.assertEqual([unit.kind for unit in units], ["speech", "break", "speech"])
        self.assertIn("World Wide Web Consortium", units[0].text)
        self.assertEqual(units[1].duration_ms, 500)
        self.assertIn("3rd", units[2].text)
        self.assertIn("A P I", units[2].text)

    def test_voice_language_and_nested_prosody_are_inherited(self):
        units = self.compile(
            """<speak>
              <voice name="ES">Hola.</voice>
              <prosody speed="0.9" pitch="+2st" volume="0.8">
                Styled.<prosody pitch="-1st" volume="1.25">Nested.</prosody>
              </prosody>
            </speak>"""
        )

        speech = [unit for unit in units if unit.kind == "speech"]
        self.assertEqual((speech[0].language, speech[0].voice), ("ES", "ES"))
        self.assertEqual(speech[1].prosody.speed, 0.9)
        self.assertEqual(speech[1].prosody.pitch_semitones, 2)
        self.assertEqual(speech[2].prosody.pitch_semitones, 1)
        self.assertEqual(speech[2].prosody.volume, 1)

    def test_explicit_zero_break_is_preserved(self):
        units = self.compile(
            '<speak><voice name="EN-BR">One.</voice><break time="0ms"/>'
            '<voice name="ES">Dos.</voice></speak>'
        )

        self.assertEqual([unit.kind for unit in units], ["speech", "break", "speech"])
        self.assertEqual(units[1].duration_ms, 0)

    def test_standard_namespace_is_accepted(self):
        units = self.compile(
            '<speak xmlns="http://www.w3.org/2001/10/synthesis">Hello.</speak>'
        )
        self.assertEqual(units[0].text, "Hello.")

    def test_root_unknown_markup_attributes_and_phonemes_are_rejected(self):
        invalid = (
            ("<voice>Hello.</voice>", "<speak> root"),
            ("<speak><emphasis>Hello.</emphasis></speak>", "Unsupported SSML element"),
            ('<speak bad="yes">Hello.</speak>', "Unsupported attribute"),
            (
                '<speak><phoneme alphabet="ipa" ph="wurld">world</phoneme></speak>',
                "not supported",
            ),
        )
        for document, message in invalid:
            with self.subTest(document=document):
                with self.assertRaisesRegex(SSMLValidationError, message):
                    self.parse(document)

    def test_unsafe_xml_and_excessive_nesting_are_rejected(self):
        with self.assertRaisesRegex(SSMLValidationError, "Invalid or unsafe SSML"):
            self.parse('<!DOCTYPE speak [<!ENTITY x "hello">]><speak>&x;</speak>')

        content = "Hello."
        for _ in range(MAX_SSML_NESTING + 1):
            content = f'<lang xml:lang="en-US">{content}</lang>'
        with self.assertRaisesRegex(SSMLValidationError, "nesting is limited"):
            self.parse(f"<speak>{content}</speak>")

    def test_break_and_prosody_limits_are_enforced(self):
        with self.assertRaisesRegex(SSMLValidationError, "Each <break>"):
            self.parse(f'<speak><break time="{MAX_BREAK_MS + 1}ms"/></speak>')
        with self.assertRaisesRegex(SSMLValidationError, "Total SSML break"):
            self.parse(
                "<speak><break time='10s'/><break time='10s'/>"
                "<break time='10s'/><break time='1ms'/></speak>"
            )
        with self.assertRaisesRegex(SSMLValidationError, "prosody"):
            self.parse('<speak><prosody speed="1.5"><prosody speed="1.5">No.</prosody></prosody></speak>')

    def test_say_as_validation_is_language_aware(self):
        with self.assertRaisesRegex(SSMLValidationError, "English models only"):
            self.parse(
                "<speak><say-as interpret-as='ordinal'>3</say-as></speak>",
                language="ES",
                voice="ES",
            )
        with self.assertRaisesRegex(SSMLValidationError, "numeric value"):
            self.parse("<speak><say-as interpret-as='number'>many</say-as></speak>")


if __name__ == "__main__":
    unittest.main()
