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
    output_format: str = Field(
        "wav",
        alias="format",
        description=(
            "Response audio format. Defaults to wav for backward compatibility. "
            "Supported: wav, mp3, flac, ogg."
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


class MetricsModel(BaseModel):
    text: str = Field("", description="Text to inspect.")
    language: str = Field("EN", description="Language/model code used for sentence splitting.")


class LanguageAction(BaseModel):
    language: str = Field(..., description="Configured language/model code.")
