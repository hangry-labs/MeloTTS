import gc
import io
import json
import logging
import os
import threading
from pathlib import Path

import soundfile as sf
import torch
from fastapi import Body, Depends, FastAPI, HTTPException, Query
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, ConfigDict, Field
from starlette.concurrency import run_in_threadpool

from melo.api import TTS
from melo.split_utils import split_sentence
from melo.standalone_ui.server import create_app as create_ui_app


APP_ROOT = Path(__file__).resolve().parent.parent


def _read_non_empty_env(name: str):
    value = os.getenv(name)
    if value is None:
        return None
    value = value.strip()
    return value or None


def _load_build_metadata():
    metadata_path = _read_non_empty_env("BUILD_METADATA_PATH") or str(APP_ROOT / ".build_meta.json")
    try:
        with open(metadata_path, "r", encoding="utf-8") as metadata_file:
            data = json.load(metadata_file)
            if isinstance(data, dict):
                return data
    except FileNotFoundError:
        pass
    except Exception as error:
        logging.getLogger("TTSApp").warning(
            f"Unable to read build metadata from {metadata_path}: {error}"
        )
    return {}


def _load_version_from_file():
    version_file_path = _read_non_empty_env("VERSION_FILE_PATH") or str(APP_ROOT / "VERSION")
    try:
        with open(version_file_path, "r", encoding="utf-8") as version_file:
            version = version_file.read().strip()
            return version or None
    except FileNotFoundError:
        pass
    except Exception as error:
        logging.getLogger("TTSApp").warning(
            f"Unable to read version file at {version_file_path}: {error}"
        )
    return None


def _resolve_runtime_version_and_build():
    metadata = _load_build_metadata()
    version = _load_version_from_file() or metadata.get("app_version") or "0.0.0-SNAPSHOT"
    build_id = metadata.get("build_id") or _read_non_empty_env("BUILD_ID") or "local-dev"
    return version, build_id


VERSION, BUILD_ID = _resolve_runtime_version_and_build()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("TTSApp")
logger.info(f"Starting TTS UI+API App - Version: {VERSION}, Build: {BUILD_ID}")


def validate_nltk_resources(required_languages):
    if not any(lang.startswith("EN") for lang in required_languages):
        return

    try:
        import nltk
    except Exception as error:
        raise RuntimeError(f"Failed to import nltk for EN startup validation: {error}") from error

    required = [
        ("taggers/averaged_perceptron_tagger_eng", "averaged_perceptron_tagger_eng"),
        ("corpora/cmudict", "cmudict"),
    ]
    missing = []
    for resource_path, resource_name in required:
        try:
            nltk.data.find(resource_path)
        except LookupError:
            missing.append(resource_name)

    if missing:
        raise RuntimeError(
            "Missing required NLTK data for EN synthesis: "
            + ", ".join(missing)
            + ". Run `python melo/init_downloads.py` or `python -m nltk.downloader "
            + "averaged_perceptron_tagger_eng cmudict` in the runtime image."
        )


def get_cuda_devices():
    if not torch.cuda.is_available():
        return []
    return [torch.cuda.get_device_name(idx) for idx in range(torch.cuda.device_count())]


def get_runtime_label():
    cuda_devices = get_cuda_devices()
    if cuda_devices:
        visible = os.getenv("CUDA_VISIBLE_DEVICES", "all")
        device_list = ", ".join(f"{idx}:{name}" for idx, name in enumerate(cuda_devices))
        return f"GPU x{len(cuda_devices)} (visible={visible}) [{device_list}]"
    try:
        mps_backend = getattr(torch.backends, "mps", None)
        if mps_backend is not None and getattr(mps_backend, "is_available", lambda: False)():
            return "Apple MPS"
    except Exception as error:
        logger.warning(f"Could not determine runtime device label: {error}")
    return "CPU"


DEVICE = os.getenv("TTS_DEVICE", "auto")
logger.info(
    f"Runtime device setting: {DEVICE}; CUDA_VISIBLE_DEVICES={os.getenv('CUDA_VISIBLE_DEVICES', 'not-set')}"
)
RUNTIME_LABEL = get_runtime_label()
logger.info(f"Runtime label: {RUNTIME_LABEL}")
LANGUAGES = [
    lang.strip()
    for lang in os.getenv("TTS_LANGUAGES", "EN,EN_V2,EN_NEWEST,ES,FR,ZH,JP,KR").split(",")
    if lang.strip()
]
validate_nltk_resources(LANGUAGES)
logger.info(f"Loading models for languages: {LANGUAGES}")
models = {}
MODEL_LOCK = threading.RLock()
for lang in LANGUAGES:
    try:
        models[lang] = TTS(language=lang, device=DEVICE)
        logger.info(f"Loaded TTS model for {lang}")
    except Exception as error:
        logger.error(f"Failed to load model for {lang}: {error}")


DEFAULT_TEXTS = {
    "EN": "The field of text-to-speech has seen rapid development recently.",
    "EN_V2": "The field of text-to-speech has seen rapid development recently.",
    "EN_NEWEST": "The field of text-to-speech has seen rapid development recently.",
    "ES": "El campo de sintesis de voz ha experimentado un rapido desarrollo recientemente.",
    "FR": "Le domaine de la synthese vocale a connu un developpement rapide recemment.",
    "ZH": "最近，文本到语音领域发展迅速。",
    "JP": "テキストから音声への分野は最近急速に発展しています。",
    "KR": "텍스트-음성 변환 분야는 최근 급격한 발전을 이루었습니다。",
}

QUOTE_BANK = {
    "EN": [
        "A clear voice can make a simple sentence feel alive.",
        "Every small test teaches the system something useful.",
        "The morning light moved slowly across the quiet room.",
        "Good tools should stay out of the way and help the work flow.",
        "Speech turns written ideas into something people can feel.",
        "A careful listener notices rhythm before individual words.",
        "The fastest path is often the one that stays simple.",
        "Today is a good day to make the interface easier to use.",
        "Strong software grows from many small and practical decisions.",
        "When the sound is natural, the text becomes easier to trust.",
    ],
    "EN_V2": [
        "A clear voice can make a simple sentence feel alive.",
        "Every small test teaches the system something useful.",
        "The morning light moved slowly across the quiet room.",
        "Good tools should stay out of the way and help the work flow.",
        "Speech turns written ideas into something people can feel.",
        "A careful listener notices rhythm before individual words.",
        "The fastest path is often the one that stays simple.",
        "Today is a good day to make the interface easier to use.",
        "Strong software grows from many small and practical decisions.",
        "When the sound is natural, the text becomes easier to trust.",
    ],
    "EN_NEWEST": [
        "A clear voice can make a simple sentence feel alive.",
        "Every small test teaches the system something useful.",
        "The morning light moved slowly across the quiet room.",
        "Good tools should stay out of the way and help the work flow.",
        "Speech turns written ideas into something people can feel.",
        "A careful listener notices rhythm before individual words.",
        "The fastest path is often the one that stays simple.",
        "Today is a good day to make the interface easier to use.",
        "Strong software grows from many small and practical decisions.",
        "When the sound is natural, the text becomes easier to trust.",
    ],
    "ES": [
        "Una voz clara puede dar vida a una frase sencilla.",
        "Cada prueba pequena ensena algo util al sistema.",
        "La luz de la manana avanzo despacio por la habitacion tranquila.",
        "Las buenas herramientas ayudan sin llamar demasiado la atencion.",
        "La voz convierte las ideas escritas en una experiencia cercana.",
        "Quien escucha con atencion percibe primero el ritmo.",
        "El camino mas rapido suele ser el que mantiene todo simple.",
        "Hoy es un buen dia para mejorar la interfaz.",
        "El buen software crece con decisiones pequenas y practicas.",
        "Cuando el sonido es natural, el texto resulta mas confiable.",
    ],
    "FR": [
        "Une voix claire peut donner vie a une phrase simple.",
        "Chaque petit test apprend quelque chose d utile au systeme.",
        "La lumiere du matin avancait lentement dans la piece calme.",
        "Les bons outils aident sans attirer trop d attention.",
        "La parole transforme les idees ecrites en experience proche.",
        "Une personne attentive remarque le rythme avant les mots.",
        "Le chemin le plus rapide reste souvent le plus simple.",
        "Aujourd hui est un bon jour pour rendre l interface plus agreable.",
        "Un bon logiciel grandit grace a de petites decisions pratiques.",
        "Quand le son parait naturel, le texte inspire davantage confiance.",
    ],
    "ZH": [
        "清晰的声音能让简单的句子变得生动。",
        "每一次小测试都会让系统学到有用的东西。",
        "清晨的光慢慢移过安静的房间。",
        "好的工具应该安静地帮助工作顺利进行。",
        "语音把写下的想法变成可以感受的内容。",
        "细心的听众会先注意到节奏。",
        "最快的道路往往是保持简单的道路。",
        "今天很适合让界面变得更好用。",
        "可靠的软件来自许多小而实际的决定。",
        "当声音自然时，文字也更容易被信任。",
    ],
    "JP": [
        "澄んだ声は、短い文にも命を吹き込みます。",
        "小さなテストのたびに、システムは役立つことを学びます。",
        "朝の光が静かな部屋をゆっくり進んでいきました。",
        "よい道具は作業を静かに支えてくれます。",
        "音声は書かれた考えを身近な体験に変えます。",
        "注意深く聞く人は、言葉より先にリズムに気づきます。",
        "いちばん速い道は、たいていシンプルな道です。",
        "今日は画面をもっと使いやすくするのに良い日です。",
        "良いソフトウェアは、小さく実用的な判断から育ちます。",
        "音が自然だと、文章も信頼しやすくなります。",
    ],
    "KR": [
        "맑은 목소리는 짧은 문장에도 생기를 줍니다.",
        "작은 테스트마다 시스템은 유용한 것을 배웁니다.",
        "아침 햇살이 조용한 방 안을 천천히 지나갔습니다.",
        "좋은 도구는 일을 조용히 도와야 합니다.",
        "음성은 글로 쓴 생각을 더 가까운 경험으로 바꿉니다.",
        "주의 깊게 듣는 사람은 단어보다 리듬을 먼저 느낍니다.",
        "가장 빠른 길은 대개 단순함을 지키는 길입니다.",
        "오늘은 인터페이스를 더 쓰기 좋게 만들기에 좋은 날입니다.",
        "좋은 소프트웨어는 작고 실용적인 결정에서 자랍니다.",
        "소리가 자연스러우면 글도 더 신뢰하기 쉬워집니다.",
    ],
}

PARAMETER_PRESETS = {
    "Balanced": {"speed": 1.0, "sdp_ratio": 0.2, "noise_scale": 0.6, "noise_scale_w": 0.8},
    "Clear narration": {"speed": 0.92, "sdp_ratio": 0.18, "noise_scale": 0.45, "noise_scale_w": 0.7},
    "Expressive": {"speed": 1.0, "sdp_ratio": 0.35, "noise_scale": 0.75, "noise_scale_w": 0.9},
    "Fast preview": {"speed": 1.2, "sdp_ratio": 0.2, "noise_scale": 0.55, "noise_scale_w": 0.75},
    "Calm": {"speed": 0.85, "sdp_ratio": 0.15, "noise_scale": 0.4, "noise_scale_w": 0.65},
}

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


class TextModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    text: str = Field(..., description="Text to synthesize.")
    speed: float = Field(1.0, ge=0.5, le=2.0, description="Speech speed multiplier.")
    language: str = Field("EN", description="Loaded language/model code.")
    speaker_id: str = Field(..., description="Speaker ID from /tts/speakers.")
    sdp_ratio: float = Field(0.2, ge=0.0, le=1.0, description="Stochastic duration predictor ratio.")
    noise_scale: float = Field(0.6, ge=0.0, le=1.5, description="Acoustic sampling noise.")
    noise_scale_w: float = Field(0.8, ge=0.0, le=1.5, description="Duration sampling noise.")
    output_format: str = Field(
        "wav",
        alias="format",
        description="Response audio format. Defaults to wav for backward compatibility. Supported: wav, mp3, flac, ogg.",
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


def get_speakers_for_language(language):
    model = models.get(language)
    if not model:
        return []
    return list(model.hps.data.spk2id.keys())


def get_text_metrics(text, language):
    text = text or ""
    words = len(text.split())
    characters = len(text)
    try:
        segments = split_sentence(text, language_str=language) if text.strip() else []
    except Exception as error:
        logger.warning(f"Could not split text for metrics: {error}")
        segments = []
    return {"characters": characters, "words": words, "segments": len(segments)}


def get_voice_inventory():
    return [
        {
            "language": language,
            "status": "loaded" if language in models else "unavailable",
            "speakers": get_speakers_for_language(language),
        }
        for language in LANGUAGES
    ]


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


UI_DEFAULT_OUTPUT_FORMAT = "mp3" if "mp3" in get_supported_output_formats() else "wav"


def get_status_payload():
    return {
        "msg": "pong",
        "type": "MeloTTS",
        "version": VERSION,
        "build_id": BUILD_ID,
        "device": DEVICE,
        "runtime": RUNTIME_LABEL,
        "configured_languages": LANGUAGES,
        "loaded_languages": list(models.keys()),
        "presets": PARAMETER_PRESETS,
        "output_formats": get_supported_output_formats(),
        "stream_formats": STREAM_FORMATS,
    }


def load_model_sync(language):
    if language not in LANGUAGES:
        raise HTTPException(status_code=404, detail=f"Language '{language}' is not configured")
    with MODEL_LOCK:
        if language not in models:
            logger.info(f"Loading TTS model for {language} on demand")
            models[language] = TTS(language=language, device=DEVICE)
        return {
            "loaded": language,
            "loaded_languages": list(models.keys()),
        }


def purge_models_sync(language):
    with MODEL_LOCK:
        keep_model = models.get(language)
        if not keep_model:
            raise HTTPException(status_code=404, detail=f"Language '{language}' is not loaded")
        removed = [lang for lang in models if lang != language]
        models.clear()
        models[language] = keep_model
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    logger.info(f"Released models from memory: {removed}. Kept: {language}")
    return {"kept": language, "removed": removed, "loaded_languages": list(models.keys())}


def get_model(body: TextModel) -> TTS:
    model = models.get(body.language)
    if not model:
        logger.error(f"Requested model not available: {body.language}")
        raise HTTPException(status_code=404, detail=f"Language '{body.language}' is not loaded")
    return model


def synthesize_to_wav_bytes(body, model):
    if not body.text.strip():
        raise HTTPException(status_code=400, detail="Text must not be empty")
    spk_id = resolve_speaker_id(body, model)

    bio = io.BytesIO()
    model.tts_to_file(
        body.text,
        spk_id,
        bio,
        speed=body.speed,
        sdp_ratio=body.sdp_ratio,
        noise_scale=body.noise_scale,
        noise_scale_w=body.noise_scale_w,
        format="wav",
    )
    bio.seek(0)
    return bio


def resolve_speaker_id(body, model):
    try:
        return model.hps.data.spk2id[body.speaker_id]
    except (AttributeError, KeyError):
        raise HTTPException(status_code=400, detail=f"Invalid speaker_id '{body.speaker_id}'")


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


api = FastAPI(
    title="TTS Service API",
    description="API documentation for the MeloTTS service",
    version=VERSION,
    openapi_url="/tts/openapi.json",
    docs_url="/tts/docs",
    redoc_url="/tts/redoc",
)


@api.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    logger.error(f"Validation error for path {request.url.path}: {exc}")
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


@api.get("/tts/ping")
async def ping():
    logger.info("/tts/ping request received")
    return {"msg": "pong", "type": "MeloTTS", "version": VERSION, "build_id": BUILD_ID}


@api.get("/tts/status")
async def status():
    logger.info("/tts/status request received")
    return get_status_payload()


@api.get("/tts/defaults")
async def defaults():
    logger.info("/tts/defaults request received")
    return {
        "texts": DEFAULT_TEXTS,
        "quotes": QUOTE_BANK,
        "presets": PARAMETER_PRESETS,
        "output_formats": {"default": "wav", "available": get_supported_output_formats()},
    }


@api.get("/tts/formats")
async def formats():
    logger.info("/tts/formats request received")
    return {"default": "wav", "formats": get_supported_output_formats(), "aliases": FORMAT_ALIASES}


@api.get("/tts/stream-formats")
async def stream_formats():
    logger.info("/tts/stream-formats request received")
    return {
        "default": "pcm_s16le",
        "formats": STREAM_FORMATS,
        "aliases": STREAM_FORMAT_ALIASES,
        "granularity": "sentence",
        "notes": [
            "The model emits complete sentence segments, not token-level audio.",
            "pcm_s16le is raw mono 16-bit little-endian PCM at the model sample rate.",
            "mp3 streams are sent as consecutive encoded sentence chunks.",
        ],
    }


@api.get("/tts/languages")
async def list_languages():
    logger.info("/tts/languages request received")
    return {"languages": LANGUAGES, "loaded_languages": list(models.keys())}


@api.get("/tts/speakers")
async def list_speakers(language: str = Query(..., description="Loaded language code")):
    logger.info(f"/tts/speakers request received for language={language}")
    model = models.get(language)
    if not model:
        logger.warning(f"Requested speakers for unknown language: {language}")
        raise HTTPException(status_code=404, detail="Language not found")
    return {"language": language, "speakers": list(model.hps.data.spk2id.keys())}


@api.get("/tts/voices")
async def voices():
    logger.info("/tts/voices request received")
    return {"voices": get_voice_inventory()}


@api.post("/tts/metrics")
async def metrics(body: MetricsModel = Body(...)):
    logger.info(f"/tts/metrics request received for language={body.language}")
    return {"language": body.language, "metrics": get_text_metrics(body.text, body.language)}


@api.post("/tts/purge")
async def purge_models(language: str = Body(..., embed=True)):
    return await run_in_threadpool(purge_models_sync, language)


@api.post("/tts/load")
async def load_model(language: str = Body(..., embed=True)):
    return await run_in_threadpool(load_model_sync, language)


async def stream_tts_audio(body: TextModel, model: TTS, route_name: str):
    logger.info(f"{route_name} request: {body}")
    try:
        output_format = normalize_output_format(body.output_format)
        bio = synthesize_to_wav_bytes(body, model)
        audio, sample_rate = sf.read(bio, dtype="float32")
        duration = len(audio) / sample_rate if sample_rate else 0
        output_bio = bio
        if output_format == "wav":
            output_bio.seek(0)
        else:
            output_bio = encode_audio_bytes(audio, sample_rate, output_format)
        format_config = OUTPUT_FORMATS[output_format]
        logger.info(
            f"Streamed TTS audio for language={body.language}, speaker={body.speaker_id}, "
            f"duration={duration:.2f}s, format={output_format}"
        )
        headers = {
            "Content-Disposition": (
                f"attachment; filename=tts_{body.language}.{format_config['extension']}"
            ),
            "X-MeloTTS-Language": body.language,
            "X-MeloTTS-Speaker": body.speaker_id,
            "X-MeloTTS-Sample-Rate": str(sample_rate),
            "X-MeloTTS-Duration": f"{duration:.3f}",
        }
        if output_format != "wav":
            headers["X-MeloTTS-Format"] = output_format
        return StreamingResponse(
            output_bio,
            media_type=format_config["media_type"],
            headers=headers,
        )
    except HTTPException:
        raise
    except Exception as error:
        logger.error(f"Error during TTS generation: {error}")
        return JSONResponse(status_code=500, content={"error": str(error)})


def iter_stream_audio(body: StreamingTextModel, model: TTS, stream_format: str, sample_rate: int, spk_id: int):
    for audio in model.iter_audio_segments(
        body.text,
        spk_id,
        speed=body.speed,
        sdp_ratio=body.sdp_ratio,
        noise_scale=body.noise_scale,
        noise_scale_w=body.noise_scale_w,
        quiet=True,
        include_silence=True,
    ):
        if stream_format == "pcm_s16le":
            yield encode_pcm_s16le(audio)
        elif stream_format == "mp3":
            yield encode_audio_bytes(audio, sample_rate, "mp3").getvalue()


async def stream_tts_audio_segments(body: StreamingTextModel, model: TTS, route_name: str):
    logger.info(f"{route_name} request: {body}")
    try:
        if not body.text.strip():
            raise HTTPException(status_code=400, detail="Text must not be empty")
        stream_format = normalize_stream_format(body.stream_format)
        spk_id = resolve_speaker_id(body, model)
        sample_rate = model.hps.data.sampling_rate
        format_config = STREAM_FORMATS[stream_format]
        media_type = format_config["media_type"].format(sample_rate=sample_rate)
        headers = {
            "Content-Disposition": (
                f"attachment; filename=tts_{body.language}_stream.{format_config['extension']}"
            ),
            "X-MeloTTS-Language": body.language,
            "X-MeloTTS-Speaker": body.speaker_id,
            "X-MeloTTS-Sample-Rate": str(sample_rate),
            "X-MeloTTS-Stream-Format": stream_format,
            "X-MeloTTS-Stream-Granularity": "sentence",
        }
        return StreamingResponse(
            iter_stream_audio(body, model, stream_format, sample_rate, spk_id),
            media_type=media_type,
            headers=headers,
        )
    except HTTPException:
        raise
    except Exception as error:
        logger.error(f"Error during streaming TTS generation: {error}")
        return JSONResponse(status_code=500, content={"error": str(error)})


@api.post("/tts/generate")
async def generate_tts(body: TextModel = Body(...), model: TTS = Depends(get_model)):
    return await stream_tts_audio(body, model, "/tts/generate")


@api.post("/tts/stream")
async def stream_tts(body: StreamingTextModel = Body(...), model: TTS = Depends(get_model)):
    return await stream_tts_audio_segments(body, model, "/tts/stream")


@api.post("/tts/convert/tts", deprecated=True)
async def convert_tts(body: TextModel = Body(...), model: TTS = Depends(get_model)):
    return await stream_tts_audio(body, model, "/tts/convert/tts")


app = create_ui_app(api_app=api)
logger.info("Mounted standalone UI at / with TTS API routes under /tts")

def main():
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8888"))
    logger.info(f"Starting server on {host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        logger.exception(f"Application crashed: {error}")
