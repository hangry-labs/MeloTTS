import sys
import zipfile
from pathlib import Path


def main():
    wheel_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "dist")
    wheels = sorted(wheel_dir.glob("melotts-*.whl"), key=lambda path: path.stat().st_mtime)
    if not wheels:
        raise SystemExit(f"No melotts wheel found in {wheel_dir}")

    wheel = wheels[-1]
    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())

    required_exact = {
        "VERSION",
        "LICENSE",
        "LICENSES/Apache-2.0.txt",
        "LICENSES/MIT-MeloTTS.txt",
        "LICENSES/MIT-Tacotron.txt",
        "THIRD_PARTY_NOTICES.md",
        "assets/melotts_favicon.webp",
        "assets/hangrylabs_logo.webp",
        "melo/ssml.py",
        "melo/standalone_ui/static/index.html",
        "melo/standalone_ui/static/app.js",
        "melo/standalone_ui/static/styles.css",
    }
    missing = sorted(required_exact - names)
    if missing:
        raise SystemExit(f"Wheel {wheel.name} is missing: {', '.join(missing)}")

    print(f"Wheel contract passed: {wheel.name} ({len(names)} files)")


if __name__ == "__main__":
    main()
