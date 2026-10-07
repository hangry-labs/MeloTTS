"""Seed persistent core assets, then replace this process with the API server."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path


def seed_persistent_assets() -> None:
    source = Path("/app/baked")
    destination = Path(os.getenv("MELOTTS_PERSISTENT_ROOT", "/app/persistent"))
    if source.is_dir():
        destination.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, destination, dirs_exist_ok=True)


if __name__ == "__main__":
    seed_persistent_assets()
    os.execv(sys.executable, [sys.executable, "./melo/app.py"])
