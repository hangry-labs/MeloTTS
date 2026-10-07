"""Persisted operator settings for optional MeloTTS language packs."""

from __future__ import annotations

import json
import logging
import os
import tempfile
from pathlib import Path
from threading import RLock
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_SETTINGS_PATH = "/app/persistent/app/settings.json"
OPTIONAL_LANGUAGES_KEY = "optional_languages"
SETTINGS_SCHEMA_VERSION_KEY = "schema_version"
SETTINGS_SCHEMA_VERSION = 1


class RuntimeSettingsStore:
    """Atomically store operator choices that must survive container upgrades."""

    def __init__(self, path: str | Path | None = None) -> None:
        configured_path = path or os.getenv("MELOTTS_SETTINGS_PATH")
        self.path = Path(configured_path or DEFAULT_SETTINGS_PATH)
        self._lock = RLock()

    def _read_unlocked(self) -> dict[str, Any]:
        if not self.path.is_file():
            return {}
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Ignoring unreadable runtime settings %s: %s", self.path, exc)
            return {}
        if not isinstance(payload, dict):
            logger.warning("Ignoring runtime settings %s: expected an object", self.path)
            return {}
        return payload

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return dict(self._read_unlocked())

    def optional_languages(self, supported: tuple[str, ...]) -> list[str]:
        configured = self.snapshot().get(OPTIONAL_LANGUAGES_KEY, [])
        if not isinstance(configured, list):
            return []
        return [language for language in supported if language in configured]

    def set_optional_languages(self, languages: list[str], supported: tuple[str, ...]) -> list[str]:
        unknown = sorted(set(languages) - set(supported))
        if unknown:
            raise ValueError(f"Unsupported optional languages: {', '.join(unknown)}")
        selected = [language for language in supported if language in languages]
        self._update(OPTIONAL_LANGUAGES_KEY, selected)
        return selected

    def _update(self, key: str, value: Any) -> None:
        with self._lock:
            payload = self._read_unlocked()
            payload[SETTINGS_SCHEMA_VERSION_KEY] = SETTINGS_SCHEMA_VERSION
            payload[key] = value
            self.path.parent.mkdir(parents=True, exist_ok=True)
            descriptor, temporary_name = tempfile.mkstemp(
                prefix=f".{self.path.name}.", suffix=".tmp", dir=self.path.parent
            )
            temporary_path = Path(temporary_name)
            try:
                with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
                    json.dump(payload, handle, indent=2, sort_keys=True)
                    handle.write("\n")
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temporary_path, self.path)
            finally:
                temporary_path.unlink(missing_ok=True)
