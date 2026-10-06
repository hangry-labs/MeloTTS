import io
import shutil
import subprocess
import threading

import numpy as np
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
    "opus": {
        "sf_format": None,
        "subtype": None,
        "media_type": "audio/ogg",
        "extension": "opus",
        "label": "Opus",
        "ffmpeg_args": ["-f", "opus", "-codec:a", "libopus", "-b:a", "96k"],
    },
    "aac": {
        "sf_format": None,
        "subtype": None,
        "media_type": "audio/aac",
        "extension": "aac",
        "label": "AAC",
        "ffmpeg_args": ["-f", "adts", "-codec:a", "aac", "-b:a", "192k"],
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
    ".opus": "opus",
    ".aac": "aac",
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
        "label": "Continuous MP3 stream",
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

SSML_IMPLICIT_PAUSE_MS = 100
SSML_SILENCE_THRESHOLD_DB = -50.0
SSML_SILENCE_RELATIVE_DB = -40.0
SSML_SILENCE_FRAME_MS = 10


def audio_effects_enabled(
    pitch_semitones=0.0,
    tempo=1.0,
    volume=1.0,
    normalize=False,
):
    return (
        abs(pitch_semitones) > 0.001
        or abs(tempo - 1.0) > 0.001
        or abs(volume - 1.0) > 0.001
        or normalize
    )


def atempo_filters(multiplier):
    filters = []
    current = multiplier
    while current > 2.0:
        filters.append("atempo=2.0")
        current /= 2.0
    while current < 0.5:
        filters.append("atempo=0.5")
        current /= 0.5
    filters.append(f"atempo={current:.6f}")
    return filters


def build_audio_effect_filters(
    sample_rate,
    pitch_semitones=0.0,
    tempo=1.0,
    volume=1.0,
    normalize=False,
):
    filters = []
    if abs(pitch_semitones) > 0.001:
        pitch_factor = 2 ** (pitch_semitones / 12)
        shifted_rate = max(1, round(sample_rate * pitch_factor))
        filters.extend([f"asetrate={shifted_rate}", f"aresample={sample_rate}"])
        filters.extend(atempo_filters(1 / pitch_factor))
    if abs(tempo - 1.0) > 0.001:
        filters.extend(atempo_filters(tempo))
    if abs(volume - 1.0) > 0.001:
        filters.append(f"volume={volume:.6f}")
    if normalize:
        filters.append("loudnorm=I=-16:TP=-1.5:LRA=11")
    return filters


def _run_ffmpeg(command, input_bytes, action):
    try:
        result = subprocess.run(command, input=input_bytes, capture_output=True, check=True)
    except FileNotFoundError as error:
        raise RuntimeError(f"ffmpeg is required to {action}") from error
    except subprocess.CalledProcessError as error:
        stderr = error.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"ffmpeg failed to {action}: {stderr}") from error
    return result.stdout


def apply_audio_effects(
    audio,
    sample_rate,
    pitch_semitones=0.0,
    tempo=1.0,
    volume=1.0,
    normalize=False,
):
    audio = np.asarray(audio, dtype=np.float32)
    if audio.size == 0 or not audio_effects_enabled(
        pitch_semitones, tempo, volume, normalize
    ):
        return audio

    source = io.BytesIO()
    sf.write(source, audio, sample_rate, format="WAV", subtype="PCM_16")
    filters = build_audio_effect_filters(
        sample_rate, pitch_semitones, tempo, volume, normalize
    )
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-f",
        "wav",
        "-i",
        "pipe:0",
        "-af",
        ",".join(filters),
        "-f",
        "f32le",
        "-acodec",
        "pcm_f32le",
        "-ac",
        "1",
        "-ar",
        str(sample_rate),
        "pipe:1",
    ]
    output = _run_ffmpeg(command, source.getvalue(), "apply audio controls")
    return np.frombuffer(output, dtype="<f4").astype(np.float32, copy=True)


def resample_audio(audio, source_rate, target_rate):
    """Resample mono float audio when an SSML plan crosses model sample rates."""
    audio = np.asarray(audio, dtype=np.float32)
    if audio.size == 0 or source_rate == target_rate:
        return audio
    import torch
    from torchaudio.functional import resample

    waveform = torch.from_numpy(audio)
    return resample(waveform, source_rate, target_rate).numpy().astype(np.float32, copy=False)


def trim_silent_audio_edges(
    audio,
    sample_rate,
    *,
    leading=False,
    trailing=False,
    threshold_db=SSML_SILENCE_THRESHOLD_DB,
    frame_ms=SSML_SILENCE_FRAME_MS,
):
    """Trim low-energy outer frames while leaving interior and recording edges intact."""
    audio = np.asarray(audio)
    if audio.size == 0 or not (leading or trailing):
        return audio
    normalized = audio.astype(np.float32, copy=False)
    frame_samples = max(1, round(sample_rate * frame_ms / 1000))
    frame_count = (len(normalized) + frame_samples - 1) // frame_samples
    padded = np.pad(normalized, (0, frame_count * frame_samples - len(normalized)))
    frames = padded.reshape(frame_count, frame_samples)
    rms = np.sqrt(np.mean(np.square(frames), axis=1))
    peak_rms = float(np.max(rms))
    absolute_threshold = 10 ** (threshold_db / 20)
    relative_threshold = peak_rms * 10 ** (SSML_SILENCE_RELATIVE_DB / 20)
    active_frames = np.flatnonzero(rms >= min(absolute_threshold, relative_threshold))
    if active_frames.size == 0:
        return audio
    start = int(active_frames[0]) * frame_samples if leading else 0
    end = (
        min((int(active_frames[-1]) + 1) * frame_samples, len(audio))
        if trailing
        else len(audio)
    )
    return audio[start:end]


def compact_ssml_speech_audio(
    audio,
    *,
    trim_leading,
    trim_trailing,
    append_implicit_pause,
    sample_rate,
):
    """Remove internal model padding and add the default SSML turn handoff."""
    compacted = trim_silent_audio_edges(
        audio,
        sample_rate,
        leading=trim_leading,
        trailing=trim_trailing,
    )
    if not append_implicit_pause:
        return compacted
    pause = np.zeros(round(SSML_IMPLICIT_PAUSE_MS * sample_rate / 1000), dtype=np.float32)
    return np.concatenate((compacted, pause))


def get_supported_output_formats():
    available_formats = sf.available_formats()
    supported = {}
    for name, config in OUTPUT_FORMATS.items():
        if config.get("ffmpeg_args"):
            if shutil.which("ffmpeg"):
                supported[name] = {
                    "label": config["label"],
                    "extension": config["extension"],
                    "media_type": config["media_type"],
                }
            continue
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
    if config.get("ffmpeg_args"):
        source = io.BytesIO()
        sf.write(source, audio, sample_rate, format="WAV", subtype="PCM_16")
        command = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "wav",
            "-i",
            "pipe:0",
            *config["ffmpeg_args"],
            "pipe:1",
        ]
        encoded = io.BytesIO(_run_ffmpeg(command, source.getvalue(), f"encode {output_format}"))
        encoded.seek(0)
        return encoded
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


def encode_mp3_stream(pcm_chunks, sample_rate, read_size=8192):
    """Encode a PCM chunk iterator as one continuous, progressively readable MP3 stream."""
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-f",
        "s16le",
        "-acodec",
        "pcm_s16le",
        "-ac",
        "1",
        "-ar",
        str(sample_rate),
        "-i",
        "pipe:0",
        "-codec:a",
        "libmp3lame",
        "-b:a",
        "128k",
        "-write_xing",
        "0",
        "-id3v2_version",
        "0",
        "-flush_packets",
        "1",
        "-f",
        "mp3",
        "pipe:1",
    ]
    try:
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
        )
    except FileNotFoundError as error:
        raise RuntimeError("ffmpeg is required to stream MP3 audio") from error

    writer_errors = []

    def write_pcm():
        try:
            for chunk in pcm_chunks:
                process.stdin.write(chunk)
                process.stdin.flush()
        except (BrokenPipeError, OSError) as error:
            if process.poll() is None:
                writer_errors.append(error)
        except Exception as error:
            writer_errors.append(error)
        finally:
            try:
                process.stdin.close()
            except (BrokenPipeError, OSError):
                pass

    writer = threading.Thread(target=write_pcm, name="melotts-mp3-writer", daemon=True)
    writer.start()
    try:
        while chunk := process.stdout.read(read_size):
            yield chunk
        writer.join()
        return_code = process.wait()
        stderr = process.stderr.read().decode("utf-8", errors="replace").strip()
        if writer_errors:
            raise RuntimeError("Failed while producing PCM for MP3 streaming") from writer_errors[0]
        if return_code:
            raise RuntimeError(f"ffmpeg failed to stream MP3 audio: {stderr}")
    finally:
        if process.poll() is None:
            process.terminate()
        writer.join(timeout=2)
        if process.poll() is None:
            process.kill()
        process.wait()
        process.stdout.close()
        process.stderr.close()
