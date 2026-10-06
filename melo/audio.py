import io

import soundfile as sf
from fastapi import HTTPException

OUTPUT_FORMATS = {
    "wav": {
        "sf_format": "WAV",
        "subtype": None,
        "media_type": "audio/wav",
        "extension": "wav",
        "label": "WAV",
    },
    "mp3": {
        "sf_format": "MP3",
        "subtype": "MPEG_LAYER_III",
        "media_type": "audio/mpeg",
        "extension": "mp3",
        "label": "MP3",
    },
    "flac": {
        "sf_format": "FLAC",
        "subtype": "PCM_16",
        "media_type": "audio/flac",
        "extension": "flac",
        "label": "FLAC",
    },
    "ogg": {
        "sf_format": "OGG",
        "subtype": "VORBIS",
        "media_type": "audio/ogg",
        "extension": "ogg",
        "label": "Ogg Vorbis",
    },
}

FORMAT_ALIASES = {
    ".wav": "wav",
    "wave": "wav",
    ".mp3": "mp3",
    "mpeg": "mp3",
    ".flac": "flac",
    ".ogg": "ogg",
    "oga": "ogg",
    "vorbis": "ogg",
}

STREAM_FORMATS = {
    "pcm_s16le": {
        "media_type": "audio/pcm;rate={sample_rate};channels=1;encoding=signed-integer;bits=16",
        "extension": "pcm",
        "label": "Raw PCM 16-bit little-endian",
    },
    "mp3": {
        "media_type": "audio/mpeg",
        "extension": "mp3",
        "label": "MP3 sentence chunks",
    },
}

STREAM_FORMAT_ALIASES = {
    "pcm": "pcm_s16le",
    "s16le": "pcm_s16le",
    "raw": "pcm_s16le",
    ".pcm": "pcm_s16le",
    ".mp3": "mp3",
    "mpeg": "mp3",
}


def get_supported_output_formats():
    available_formats = sf.available_formats()
    supported = {}
    for name, config in OUTPUT_FORMATS.items():
        if config["sf_format"] not in available_formats:
            continue
        subtype = config["subtype"]
        if subtype and subtype not in sf.available_subtypes(config["sf_format"]):
            continue
        supported[name] = {
            "label": config["label"],
            "extension": config["extension"],
            "media_type": config["media_type"],
        }
    return supported


def normalize_output_format(output_format):
    normalized = (output_format or "wav").strip().lower()
    normalized = FORMAT_ALIASES.get(normalized, normalized)
    if normalized not in OUTPUT_FORMATS:
        supported = ", ".join(get_supported_output_formats().keys())
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported output format '{output_format}'. Supported formats: {supported}",
        )
    if normalized not in get_supported_output_formats():
        raise HTTPException(
            status_code=500,
            detail=f"Output format '{normalized}' is configured but not available in this runtime",
        )
    return normalized


def normalize_stream_format(stream_format):
    normalized = (stream_format or "pcm_s16le").strip().lower()
    normalized = STREAM_FORMAT_ALIASES.get(normalized, normalized)
    if normalized not in STREAM_FORMATS:
        supported = ", ".join(STREAM_FORMATS.keys())
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported stream_format '{stream_format}'. Supported formats: {supported}",
        )
    if normalized == "mp3" and "mp3" not in get_supported_output_formats():
        raise HTTPException(
            status_code=500,
            detail="MP3 streaming is configured but MP3 encoding is not available in this runtime",
        )
    return normalized


def encode_audio_bytes(audio, sample_rate, output_format):
    config = OUTPUT_FORMATS[output_format]
    encoded = io.BytesIO()
    sf.write(
        encoded,
        audio,
        sample_rate,
        format=config["sf_format"],
        subtype=config["subtype"],
    )
    encoded.seek(0)
    return encoded


def encode_pcm_s16le(audio):
    clamped = audio.clip(-1.0, 1.0)
    return (clamped * 32767.0).astype("<i2").tobytes()
