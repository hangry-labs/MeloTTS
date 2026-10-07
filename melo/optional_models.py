"""Catalog and explicit downloader for optional language model packs."""

from __future__ import annotations

import gc
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any

from melo.model_registry import (
    BERT_MODEL_REVISIONS,
    TTS_MODEL_REPOSITORIES,
    TTS_MODEL_REVISIONS,
)

CORE_FULL_LANGUAGES = ("EN", "EN_V2", "EN_NEWEST", "FR", "ZH", "JP")
ENGLISH_LANGUAGES = ("EN", "EN_V2", "EN_NEWEST")

OPTIONAL_LANGUAGE_PACKS: dict[str, dict[str, str]] = {
    "ES": {
        "name": "Spanish",
        "encoder_id": "dccuchile/bert-base-spanish-wwm-uncased",
        "terms_url": "https://huggingface.co/dccuchile/bert-base-spanish-wwm-uncased",
        "warning": (
            "BETO describes CC BY 4.0 as its intended license but warns that some "
            "training data may have incompatible terms, especially for commercial use."
        ),
    },
    "KR": {
        "name": "Korean",
        "encoder_id": "kykim/bert-kor-base",
        "terms_url": "https://huggingface.co/kykim/bert-kor-base",
        "warning": (
            "The kykim/bert-kor-base model card does not declare a model license. "
            "Confirm that its terms fit your use before downloading."
        ),
    },
}
OPTIONAL_LANGUAGE_CODES = tuple(OPTIONAL_LANGUAGE_PACKS)

_INSTALL_LOCK = RLock()


def _persistent_root() -> Path:
    configured = os.getenv("MELOTTS_PERSISTENT_ROOT", "/app/persistent")
    return Path(configured)


def _marker_path(language: str) -> Path:
    return _persistent_root() / "app" / "model-packs" / f"{language}.json"


def _hub_cache() -> Path:
    configured = os.getenv("HF_HUB_CACHE")
    if configured:
        return Path(configured)
    hf_home = Path(os.getenv("HF_HOME", Path.home() / ".cache" / "huggingface"))
    return hf_home / "hub"


def _expected_marker(language: str) -> dict[str, str]:
    pack = OPTIONAL_LANGUAGE_PACKS[language]
    encoder_id = pack["encoder_id"]
    return {
        "language": language,
        "tts_repo_id": TTS_MODEL_REPOSITORIES[language],
        "tts_revision": TTS_MODEL_REVISIONS[language],
        "encoder_id": encoder_id,
        "encoder_revision": BERT_MODEL_REVISIONS[encoder_id],
    }


def optional_pack_installed(language: str) -> bool:
    if language not in OPTIONAL_LANGUAGE_PACKS:
        return False
    marker_path = _marker_path(language)
    try:
        marker = json.loads(marker_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    expected = _expected_marker(language)
    if any(marker.get(key) != value for key, value in expected.items()):
        return False

    try:
        from huggingface_hub import try_to_load_from_cache
    except ImportError:
        return True

    cache_dir = str(_hub_cache())

    def cached(repo_id: str, filename: str, revision: str) -> bool:
        return isinstance(
            try_to_load_from_cache(
                repo_id,
                filename,
                revision=revision,
                cache_dir=cache_dir,
            ),
            str,
        )

    tts_ready = all(
        cached(expected["tts_repo_id"], filename, expected["tts_revision"])
        for filename in ("config.json", "checkpoint.pth")
    )
    encoder_ready = all(
        cached(expected["encoder_id"], filename, expected["encoder_revision"])
        for filename in ("config.json", "tokenizer_config.json", "vocab.txt")
    ) and any(
        cached(expected["encoder_id"], filename, expected["encoder_revision"])
        for filename in ("model.safetensors", "pytorch_model.bin")
    )
    return tts_ready and encoder_ready


def optional_pack_inventory(enabled: set[str]) -> list[dict[str, Any]]:
    return [
        {
            "language": language,
            **pack,
            "enabled": language in enabled,
            "installed": optional_pack_installed(language),
            "persistent": True,
            "requires_internet_for_first_download": True,
        }
        for language, pack in OPTIONAL_LANGUAGE_PACKS.items()
    ]


def _write_marker(language: str) -> None:
    marker_path = _marker_path(language)
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{marker_path.name}.", suffix=".tmp", dir=marker_path.parent
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            marker = {
                **_expected_marker(language),
                "terms_accepted_at_utc": datetime.now(timezone.utc)
                .replace(microsecond=0)
                .isoformat()
                .replace("+00:00", "Z"),
            }
            json.dump(marker, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, marker_path)
    finally:
        temporary_path.unlink(missing_ok=True)


def install_optional_pack(language: str) -> None:
    """Download and verify one optional pack after explicit operator consent."""
    if language not in OPTIONAL_LANGUAGE_PACKS:
        raise ValueError(f"Unsupported optional language: {language}")

    with _INSTALL_LOCK:
        if optional_pack_installed(language):
            return

        from huggingface_hub import hf_hub_download
        from transformers import AutoModelForMaskedLM, AutoTokenizer

        cache_dir = str(_hub_cache())
        tts_repo = TTS_MODEL_REPOSITORIES[language]
        tts_revision = TTS_MODEL_REVISIONS[language]
        for filename in ("config.json", "checkpoint.pth"):
            hf_hub_download(
                repo_id=tts_repo,
                filename=filename,
                revision=tts_revision,
                cache_dir=cache_dir,
                local_files_only=False,
            )

        encoder_id = OPTIONAL_LANGUAGE_PACKS[language]["encoder_id"]
        encoder_revision = BERT_MODEL_REVISIONS[encoder_id]
        tokenizer = AutoTokenizer.from_pretrained(
            encoder_id,
            revision=encoder_revision,
            cache_dir=cache_dir,
            local_files_only=False,
        )
        model = AutoModelForMaskedLM.from_pretrained(
            encoder_id,
            revision=encoder_revision,
            cache_dir=cache_dir,
            local_files_only=False,
            from_tf=False,
        )
        del tokenizer, model
        gc.collect()
        _write_marker(language)


def release_optional_encoder(language: str) -> None:
    """Release an optional encoder that may have been loaded during synthesis."""
    if language == "ES":
        module = sys.modules.get("melo.text.spanish_bert")
        if module is not None:
            module.model = None
    elif language == "KR":
        bert_module = sys.modules.get("melo.text.japanese_bert")
        language_module = sys.modules.get("melo.text.korean")
        if bert_module is not None and language_module is not None:
            bert_module.models.pop(language_module.model_id, None)
            bert_module.tokenizers.pop(language_module.model_id, None)
