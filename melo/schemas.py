from pydantic import BaseModel, ConfigDict, Field


class TextModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    text: str = Field(..., description="Text to synthesize.")
    speed: float = Field(1.0, ge=0.5, le=2.0, description="Speech speed multiplier.")
    language: str = Field("EN", description="Loaded language/model code.")
    speaker_id: str = Field(..., description="Speaker ID from /tts/speakers.")
    sdp_ratio: float = Field(
        0.2,
        ge=0.0,
        le=1.0,
        description="Stochastic duration predictor ratio.",
    )
    noise_scale: float = Field(
        0.6,
        ge=0.0,
        le=1.5,
        description="Acoustic sampling noise.",
    )
    noise_scale_w: float = Field(
        0.8,
        ge=0.0,
        le=1.5,
        description="Duration sampling noise.",
    )
    pitch_semitones: float = Field(
        0.0,
        ge=-12.0,
        le=12.0,
        description=(
            "Optional post-synthesis pitch shift in semitones. "
            "Zero skips pitch processing."
        ),
    )
    tempo: float = Field(
        1.0,
        ge=0.5,
        le=2.0,
        description="Optional post-synthesis tempo multiplier. One skips tempo processing.",
    )
    volume: float = Field(
        1.0,
        ge=0.0,
        le=2.0,
        description="Optional output volume multiplier. One skips volume processing.",
    )
    normalize: bool = Field(
        False,
        description="Apply FFmpeg loudness normalization after synthesis.",
    )
    output_format: str = Field(
        "wav",
        alias="format",
        description=(
            "Response audio format. Defaults to wav for backward compatibility. "
            "Supported: wav, mp3, flac, ogg, opus, aac."
        ),
    )


class StreamingTextModel(TextModel):
    stream_format: str = Field(
        "pcm_s16le",
        description=(
            "Streaming response format. Defaults to raw PCM for true chunked streaming. "
            "Supported: pcm_s16le, mp3."
        ),
    )


class OpenAISpeechRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model: str = Field(..., min_length=1, description="OpenAI-compatible Melo model ID.")
    input: str = Field(..., min_length=1, description="Text to synthesize.")
    voice: str | dict[str, str] = Field(
        ..., description="Melo speaker ID returned by /v1/audio/voices."
    )
    response_format: str = Field(
        "mp3", description="Supported: mp3, opus, aac, flac, wav, pcm."
    )
    speed: float = Field(1.0, ge=0.25, le=4.0)
    instructions: str | None = Field(
        None, description="Reserved for OpenAI compatibility; not supported by MeloTTS."
    )
    stream_format: str = Field(
        "audio", description="Only the OpenAI audio stream format is supported."
    )


class MetricsModel(BaseModel):
    text: str = Field("", description="Text to inspect.")
    language: str = Field("EN", description="Language/model code used for sentence splitting.")


class LanguageAction(BaseModel):
    language: str = Field(..., description="Configured language/model code.")
