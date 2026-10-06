"""Bounded experimental SSML parsing and synthesis-plan compilation."""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from math import isfinite
from typing import Literal

from defusedxml import ElementTree
from defusedxml.common import DefusedXmlException

SSML_NAMESPACE = "http://www.w3.org/2001/10/synthesis"
XML_LANGUAGE_ATTRIBUTE = "{http://www.w3.org/XML/1998/namespace}lang"
MAX_SSML_CHARACTERS = 50_000
MAX_SSML_ELEMENTS = 256
MAX_SSML_NESTING = 8
MAX_BREAK_MS = 10_000
MAX_TOTAL_BREAK_MS = 30_000
MAX_ORDINAL_DIGITS = 18

_BREAK_PATTERN = re.compile(r"^(\d+(?:\.\d+)?)\s*(ms|s)$")
_MULTIPLIER_PATTERN = re.compile(r"^[+]?(?:\d+(?:\.\d*)?|\.\d+)$")
_PITCH_PATTERN = re.compile(r"^([+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*(?:st)?$")
_INTEGER_PATTERN = re.compile(r"^\d+$")
_NUMBER_PATTERN = re.compile(r"^[+-]?\d+(?:[.,]\d+)?$")

MIN_SPEED = 0.5
MAX_SPEED = 2.0
MIN_PITCH_SEMITONES = -12.0
MAX_PITCH_SEMITONES = 12.0
MIN_TEMPO = 0.5
MAX_TEMPO = 2.0
MIN_VOLUME = 0.0
MAX_VOLUME = 2.0


class SSMLValidationError(ValueError):
    """Raised when experimental SSML input is malformed or unsupported."""


@dataclass(frozen=True)
class SSMLProsody:
    speed: float = 1.0
    pitch_semitones: float = 0.0
    tempo: float = 1.0
    volume: float = 1.0


@dataclass(frozen=True)
class SSMLSegment:
    kind: Literal["text", "break"]
    value: str = ""
    duration_ms: int = 0
    language: str = ""
    voice: str = ""
    prosody: SSMLProsody = SSMLProsody()


@dataclass(frozen=True)
class SSMLSynthesisUnit:
    kind: Literal["speech", "break"]
    text: str = ""
    duration_ms: int = 0
    language: str = ""
    voice: str = ""
    prosody: SSMLProsody = SSMLProsody()


@dataclass(frozen=True)
class _SSMLContext:
    language: str
    voice: str
    language_explicit: bool = False
    prosody: SSMLProsody = SSMLProsody()


def _tag_name(tag: str) -> str:
    if tag.startswith("{"):
        namespace, separator, local_name = tag[1:].partition("}")
        if not separator or namespace != SSML_NAMESPACE:
            raise SSMLValidationError(f"Unsupported SSML namespace '{namespace}'.")
        return local_name
    return tag


def _require_attributes(element, allowed: set[str]) -> None:
    unknown = sorted(set(element.attrib) - allowed)
    if unknown:
        name = _tag_name(element.tag)
        raise SSMLValidationError(
            f"Unsupported attribute on <{name}>: {', '.join(unknown)}."
        )


def _plain_content(element, tag: str) -> str:
    if list(element):
        raise SSMLValidationError(f"Nested tags are not supported inside <{tag}>.")
    return element.text or ""


def _append_text(segments: list[SSMLSegment], value: str, context: _SSMLContext) -> None:
    if not value:
        return
    if (
        segments
        and segments[-1].kind == "text"
        and segments[-1].language == context.language
        and segments[-1].voice == context.voice
        and segments[-1].prosody == context.prosody
    ):
        previous = segments[-1]
        segments[-1] = SSMLSegment(
            "text",
            previous.value + value,
            language=context.language,
            voice=context.voice,
            prosody=context.prosody,
        )
        return
    segments.append(
        SSMLSegment(
            "text",
            value,
            language=context.language,
            voice=context.voice,
            prosody=context.prosody,
        )
    )


def _optional_multiplier(value: str, attribute: str) -> float:
    normalized = value.strip()
    if not normalized:
        return 1.0
    if not _MULTIPLIER_PATTERN.fullmatch(normalized):
        raise SSMLValidationError(
            f"<prosody {attribute}> must be a positive numeric multiplier."
        )
    multiplier = float(normalized)
    if not isfinite(multiplier):
        raise SSMLValidationError(
            f"<prosody {attribute}> must be a finite numeric multiplier."
        )
    return multiplier


def _optional_pitch(value: str) -> float:
    normalized = value.strip()
    if not normalized:
        return 0.0
    match = _PITCH_PATTERN.fullmatch(normalized)
    if not match:
        raise SSMLValidationError(
            "<prosody pitch> must use semitones, for example +2st or -1.5st."
        )
    pitch = float(match.group(1))
    if not isfinite(pitch):
        raise SSMLValidationError("<prosody pitch> must be finite.")
    return pitch


def _validate_prosody(prosody: SSMLProsody) -> SSMLProsody:
    ranges = (
        ("speed", prosody.speed, MIN_SPEED, MAX_SPEED),
        ("pitch", prosody.pitch_semitones, MIN_PITCH_SEMITONES, MAX_PITCH_SEMITONES),
        ("tempo", prosody.tempo, MIN_TEMPO, MAX_TEMPO),
        ("volume", prosody.volume, MIN_VOLUME, MAX_VOLUME),
    )
    for name, value, minimum, maximum in ranges:
        if not minimum <= value <= maximum:
            raise SSMLValidationError(
                f"Effective <prosody {name}> must be between {minimum:g} and {maximum:g}."
            )
    return prosody


def _prosody_context(element, context: _SSMLContext) -> _SSMLContext:
    _require_attributes(element, {"speed", "pitch", "tempo", "volume"})
    current = context.prosody
    prosody = _validate_prosody(
        SSMLProsody(
            speed=current.speed
            * _optional_multiplier(element.attrib.get("speed", ""), "speed"),
            pitch_semitones=current.pitch_semitones
            + _optional_pitch(element.attrib.get("pitch", "")),
            tempo=current.tempo
            * _optional_multiplier(element.attrib.get("tempo", ""), "tempo"),
            volume=current.volume
            * _optional_multiplier(element.attrib.get("volume", ""), "volume"),
        )
    )
    return _SSMLContext(
        context.language,
        context.voice,
        context.language_explicit,
        prosody,
    )


def _parse_break_ms(value: str) -> int:
    match = _BREAK_PATTERN.fullmatch(value.strip())
    if not match:
        raise SSMLValidationError(
            "<break time> must use seconds or milliseconds, for example 500ms or 1.5s."
        )
    amount = float(match.group(1))
    multiplier = 1000 if match.group(2) == "s" else 1
    if not isfinite(amount) or amount * multiplier > MAX_BREAK_MS:
        raise SSMLValidationError(
            f"Each <break> is limited to {MAX_BREAK_MS / 1000:g} seconds."
        )
    return round(amount * multiplier)


def _english_ordinal(value: str) -> str:
    number = int(value)
    remainder = number % 100
    if 10 <= remainder <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(number % 10, "th")
    return f"{number}{suffix}"


def _say_as(value: str, interpretation: str, language: str) -> str:
    content = value.strip()
    if not content:
        raise SSMLValidationError("<say-as> content must not be empty.")
    if interpretation == "characters":
        return " ".join(content)
    if interpretation == "number":
        if not _NUMBER_PATTERN.fullmatch(content):
            raise SSMLValidationError(
                "<say-as interpret-as='number'> requires a numeric value."
            )
        return content
    if interpretation == "ordinal":
        if not language.startswith("EN"):
            raise SSMLValidationError(
                "Experimental ordinal <say-as> currently supports English models only."
            )
        if not _INTEGER_PATTERN.fullmatch(content):
            raise SSMLValidationError(
                "<say-as interpret-as='ordinal'> requires a non-negative integer."
            )
        if len(content) > MAX_ORDINAL_DIGITS:
            raise SSMLValidationError(
                f"Experimental ordinal values are limited to {MAX_ORDINAL_DIGITS} digits."
            )
        return _english_ordinal(content)
    raise SSMLValidationError(
        "Unsupported <say-as interpret-as> value. Use characters, number, or ordinal."
    )


def parse_ssml(
    document: str,
    language: str,
    *,
    default_voice: str,
    resolve_language: Callable[[str], str],
    resolve_voice_language: Callable[[str], str],
) -> list[SSMLSegment]:
    """Parse the supported SSML subset without loading models or producing audio."""
    if len(document) > MAX_SSML_CHARACTERS:
        raise SSMLValidationError(
            f"Experimental SSML input is limited to {MAX_SSML_CHARACTERS} characters."
        )
    try:
        root = ElementTree.fromstring(
            document,
            forbid_dtd=True,
            forbid_entities=True,
            forbid_external=True,
        )
    except (ElementTree.ParseError, DefusedXmlException) as exc:
        raise SSMLValidationError(f"Invalid or unsafe SSML: {exc}") from exc

    if _tag_name(root.tag) != "speak":
        raise SSMLValidationError("SSML input must have one <speak> root element.")
    _require_attributes(root, {"version", XML_LANGUAGE_ATTRIBUTE})
    if root.attrib.get("version", "1.0") != "1.0":
        raise SSMLValidationError("Only SSML version 1.0 is supported.")
    if sum(1 for _ in root.iter()) > MAX_SSML_ELEMENTS:
        raise SSMLValidationError(
            f"Experimental SSML is limited to {MAX_SSML_ELEMENTS} elements."
        )

    root_language = language
    root_language_explicit = False
    if XML_LANGUAGE_ATTRIBUTE in root.attrib:
        try:
            root_language = resolve_language(root.attrib[XML_LANGUAGE_ATTRIBUTE])
        except ValueError as exc:
            raise SSMLValidationError(str(exc)) from exc
        root_language_explicit = True

    segments: list[SSMLSegment] = []
    total_break_ms = 0
    root_context = _SSMLContext(root_language, default_voice, root_language_explicit)

    def append_children(parent, context: _SSMLContext, depth: int) -> None:
        nonlocal total_break_ms
        if depth > MAX_SSML_NESTING:
            raise SSMLValidationError(
                f"Experimental SSML nesting is limited to {MAX_SSML_NESTING} levels."
            )
        _append_text(segments, parent.text or "", context)
        for element in parent:
            tag = _tag_name(element.tag)
            if tag == "break":
                _require_attributes(element, {"time"})
                if list(element) or (element.text and element.text.strip()):
                    raise SSMLValidationError("<break> must be empty.")
                if "time" not in element.attrib:
                    raise SSMLValidationError("<break> requires a time attribute.")
                duration_ms = _parse_break_ms(element.attrib["time"])
                total_break_ms += duration_ms
                if total_break_ms > MAX_TOTAL_BREAK_MS:
                    raise SSMLValidationError(
                        f"Total SSML break time is limited to {MAX_TOTAL_BREAK_MS / 1000:g} seconds."
                    )
                segments.append(
                    SSMLSegment(
                        "break",
                        duration_ms=duration_ms,
                        language=context.language,
                        voice=context.voice,
                        prosody=context.prosody,
                    )
                )
            elif tag == "phoneme":
                raise SSMLValidationError(
                    "<phoneme> is not supported because Melo language models do not expose "
                    "a safe direct-IPA input boundary."
                )
            elif tag == "sub":
                _require_attributes(element, {"alias"})
                _plain_content(element, tag)
                alias = element.attrib.get("alias", "").strip()
                if not alias:
                    raise SSMLValidationError("<sub> requires a non-empty alias attribute.")
                _append_text(segments, alias, context)
            elif tag == "say-as":
                _require_attributes(element, {"interpret-as"})
                content = _plain_content(element, tag)
                _append_text(
                    segments,
                    _say_as(content, element.attrib.get("interpret-as", ""), context.language),
                    context,
                )
            elif tag == "lang":
                _require_attributes(element, {XML_LANGUAGE_ATTRIBUTE})
                requested_language = element.attrib.get(XML_LANGUAGE_ATTRIBUTE, "")
                if not requested_language.strip():
                    raise SSMLValidationError("<lang> requires an xml:lang attribute.")
                try:
                    resolved_language = resolve_language(requested_language)
                except ValueError as exc:
                    raise SSMLValidationError(str(exc)) from exc
                append_children(
                    element,
                    _SSMLContext(resolved_language, context.voice, True, context.prosody),
                    depth + 1,
                )
            elif tag == "voice":
                _require_attributes(element, {"name"})
                requested_voice = element.attrib.get("name", "").strip()
                if not requested_voice:
                    raise SSMLValidationError("<voice> requires a non-empty name attribute.")
                try:
                    voice_language = resolve_voice_language(requested_voice)
                except ValueError as exc:
                    raise SSMLValidationError(str(exc)) from exc
                append_children(
                    element,
                    _SSMLContext(
                        context.language if context.language_explicit else voice_language,
                        requested_voice,
                        context.language_explicit,
                        context.prosody,
                    ),
                    depth + 1,
                )
            elif tag == "prosody":
                append_children(element, _prosody_context(element, context), depth + 1)
            else:
                raise SSMLValidationError(f"Unsupported SSML element <{tag}>.")
            _append_text(segments, element.tail or "", context)

    append_children(root, root_context, 0)
    if not segments:
        raise SSMLValidationError("SSML input must contain speech or a break.")
    return segments


def compile_ssml(
    document: str,
    language: str,
    *,
    default_voice: str,
    resolve_language: Callable[[str], str],
    resolve_voice_language: Callable[[str], str],
) -> list[SSMLSynthesisUnit]:
    """Compile SSML into ordered, model-independent speech and break units."""
    units: list[SSMLSynthesisUnit] = []
    for segment in parse_ssml(
        document,
        language,
        default_voice=default_voice,
        resolve_language=resolve_language,
        resolve_voice_language=resolve_voice_language,
    ):
        if segment.kind == "break":
            units.append(
                SSMLSynthesisUnit(
                    "break",
                    duration_ms=segment.duration_ms,
                    language=segment.language,
                    voice=segment.voice,
                    prosody=segment.prosody,
                )
            )
            continue
        if not segment.value.strip():
            continue
        if (
            units
            and units[-1].kind == "speech"
            and units[-1].language == segment.language
            and units[-1].voice == segment.voice
            and units[-1].prosody == segment.prosody
        ):
            previous = units[-1]
            units[-1] = SSMLSynthesisUnit(
                "speech",
                text=previous.text + segment.value,
                language=segment.language,
                voice=segment.voice,
                prosody=segment.prosody,
            )
        else:
            units.append(
                SSMLSynthesisUnit(
                    "speech",
                    text=segment.value,
                    language=segment.language,
                    voice=segment.voice,
                    prosody=segment.prosody,
                )
            )
    if not units:
        raise SSMLValidationError("SSML input must contain speech or a break.")
    return units
