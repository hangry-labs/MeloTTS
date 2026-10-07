"""OpenAI speech API request mapping, authentication, and errors."""

from __future__ import annotations

import hmac
import os
from collections.abc import Iterable, Mapping

from fastapi import Request
from fastapi.responses import JSONResponse

from melo.schemas import OpenAISpeechRequest, StreamingTextModel, TextModel

OPENAI_MODEL_ID = "melotts"
OPENAI_GENERIC_MODEL_ALIASES = {
    "melo",
    "melo-tts",
    "melotts",
    "tts-1",
    "tts-1-hd",
}
OPENAI_RESPONSE_FORMATS = {"mp3", "opus", "aac", "flac", "wav", "pcm"}
OPENAI_STREAMING_FORMATS = {"mp3": "mp3", "pcm": "pcm_s16le"}
OPENAI_LANGUAGE_PRIORITY = ("EN_NEWEST", "EN_V2", "EN", "ES", "FR", "ZH", "JP", "KR")


class OpenAIAPIError(Exception):
    def __init__(
        self,
        message: str,
        *,
        status_code: int = 400,
        error_type: str = "invalid_request_error",
        param: str | None = None,
        code: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_type = error_type
        self.param = param
        self.code = code
        self.headers = headers or {}


def openai_error_response(
    message: str,
    *,
    status_code: int = 400,
    error_type: str = "invalid_request_error",
    param: str | None = None,
    code: str | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "message": message,
                "type": error_type,
                "param": param,
                "code": code,
            }
        },
        headers=headers,
    )


def require_openai_api_key(request: Request) -> None:
    configured_key = os.getenv("MELOTTS_API_KEY", "").strip()
    if not configured_key:
        return
    authorization = request.headers.get("authorization", "")
    scheme, _, provided_key = authorization.partition(" ")
    if scheme.lower() != "bearer" or not hmac.compare_digest(provided_key, configured_key):
        raise OpenAIAPIError(
            "Incorrect API key provided.",
            status_code=401,
            error_type="authentication_error",
            code="invalid_api_key",
            headers={"WWW-Authenticate": "Bearer"},
        )


def openai_model_id(language: str) -> str:
    return f"{OPENAI_MODEL_ID}-{language.lower().replace('_', '-')}"


def resolve_openai_model_language(model: str, configured_languages: Iterable[str]) -> str | None:
    normalized = model.strip().lower().replace("_", "-")
    if normalized in OPENAI_GENERIC_MODEL_ALIASES:
        return None
    for language in configured_languages:
        if normalized == openai_model_id(language):
            return language
    raise OpenAIAPIError(
        f"The model '{model}' does not exist.",
        param="model",
        code="model_not_found",
    )


def openai_model_object(model: str, configured_languages: Iterable[str]) -> dict[str, str]:
    language = resolve_openai_model_language(model, configured_languages)
    model_id = OPENAI_MODEL_ID if language is None else openai_model_id(language)
    return {"id": model_id, "object": "model", "owned_by": "hangry-labs"}


def openai_model_list(configured_languages: Iterable[str]) -> list[dict[str, str]]:
    configured_languages = sorted(configured_languages, key=_language_rank)
    return [
        {"id": OPENAI_MODEL_ID, "object": "model", "owned_by": "hangry-labs"},
        *[
            {
                "id": openai_model_id(language),
                "object": "model",
                "owned_by": "hangry-labs",
            }
            for language in configured_languages
        ],
    ]


def _language_rank(language: str) -> tuple[int, str]:
    try:
        return OPENAI_LANGUAGE_PRIORITY.index(language), language
    except ValueError:
        return len(OPENAI_LANGUAGE_PRIORITY), language


def order_openai_languages(languages: Iterable[str]) -> list[str]:
    return sorted(languages, key=_language_rank)


def resolve_openai_voice_language(
    model: str,
    voice: str | dict[str, str],
    configured_languages: Iterable[str],
    speakers_by_language: Mapping[str, Iterable[str]],
) -> tuple[str, str]:
    if not isinstance(voice, str):
        raise OpenAIAPIError(
            "Custom voice objects are not supported; use a Melo speaker ID.",
            param="voice",
            code="unsupported_voice",
        )
    requested_voice = voice.strip()
    if not requested_voice:
        raise OpenAIAPIError(
            "Voice must not be empty.",
            param="voice",
            code="unsupported_voice",
        )

    language = resolve_openai_model_language(model, configured_languages)
    if language is not None:
        if language not in speakers_by_language:
            raise OpenAIAPIError(
                f"Model '{openai_model_id(language)}' is configured but not loaded.",
                status_code=409,
                param="model",
                code="model_not_loaded",
            )
        if requested_voice not in speakers_by_language[language]:
            raise OpenAIAPIError(
                f"Voice '{voice}' is not available for model '{openai_model_id(language)}'.",
                param="voice",
                code="unsupported_voice",
            )
        return language, requested_voice

    candidates = [
        candidate
        for candidate, speakers in speakers_by_language.items()
        if requested_voice in speakers
    ]
    if not candidates:
        raise OpenAIAPIError(
            f"Voice '{voice}' is not served by a loaded Melo model.",
            param="voice",
            code="unsupported_voice",
        )
    return min(candidates, key=_language_rank), requested_voice


def openai_speed_controls(speed: float) -> tuple[float, float]:
    model_speed = min(2.0, max(0.5, speed))
    return model_speed, speed / model_speed


def openai_tts_request(
    payload: OpenAISpeechRequest,
    configured_languages: Iterable[str],
    speakers_by_language: Mapping[str, Iterable[str]],
) -> tuple[TextModel | StreamingTextModel, str]:
    language, voice = resolve_openai_voice_language(
        payload.model,
        payload.voice,
        configured_languages,
        speakers_by_language,
    )
    response_format = payload.response_format.strip().lower()
    if response_format not in OPENAI_RESPONSE_FORMATS:
        supported = ", ".join(sorted(OPENAI_RESPONSE_FORMATS))
        raise OpenAIAPIError(
            f"Unsupported response_format '{payload.response_format}'. Supported formats: {supported}",
            param="response_format",
            code="unsupported_format",
        )
    if payload.instructions and payload.instructions.strip():
        raise OpenAIAPIError(
            "The instructions parameter is not supported by Melo TTS.",
            param="instructions",
            code="unsupported_parameter",
        )
    if payload.stream_format.strip().lower() != "audio":
        raise OpenAIAPIError(
            "Only stream_format='audio' is supported. SSE speech events are not implemented.",
            param="stream_format",
            code="unsupported_parameter",
        )

    model_speed, tempo = openai_speed_controls(payload.speed)
    request_values = {
        "text": payload.input,
        "language": language,
        "speaker_id": voice,
        "speed": model_speed,
        "tempo": tempo,
    }
    stream_format = OPENAI_STREAMING_FORMATS.get(response_format)
    if stream_format:
        return StreamingTextModel(**request_values, stream_format=stream_format), language
    return TextModel(**request_values, format=response_format), language
