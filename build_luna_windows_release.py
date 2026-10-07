r"""
LUNA Windows Release Builder
Phase 14.7 - PyInstaller ONEDIR build

Run from:
    C:\Users\shaik\Downloads\program\project\LUNA

Command:
    python build_luna_windows_release.py

Output:
    dist\LUNA\LUNA.exe

This intentionally builds ONEDIR first because it is easier to diagnose
missing DLLs/data files than a one-file executable.
"""

from __future__ import annotations

import importlib
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DIST_DIR = ROOT / "dist"
BUILD_DIR = ROOT / "build"
SPEC_FILE = ROOT / "LUNA.spec"
APP_NAME = "LUNA"


def collect_optional_data():
    """Collect project folders that may contain runtime assets."""
    data = []

    candidates = (
        ROOT / "assets",
        ROOT / "ui" / "assets",
        ROOT / "resources",
        ROOT / "web" / "assets",
    )

    for path in candidates:
        if path.exists() and path.is_dir():
            data.append((str(path), path.relative_to(ROOT).as_posix()))

    return data


def main() -> int:
    print("=" * 78)
    print("🌙 LUNA PHASE 14.7 - WINDOWS RELEASE BUILD")
    print("=" * 78)
    print(f"PROJECT ROOT: {ROOT}")
    print(f"PYTHON: {sys.version.split()[0]}")

    try:
        pyinstaller = importlib.import_module("PyInstaller")
    except Exception as error:
        print(f"❌ PyInstaller is unavailable: {error}")
        return 1

    print(f"PYINSTALLER: {getattr(pyinstaller, '__version__', 'unknown')}")

    if not (ROOT / "main_ui.py").is_file():
        print("❌ main_ui.py not found.")
        return 1

    # Clean previous build output.
    for path in (BUILD_DIR, DIST_DIR):
        if path.exists():
            print(f"Cleaning: {path}")
            shutil.rmtree(path, ignore_errors=True)

    if SPEC_FILE.exists():
        SPEC_FILE.unlink()

    # The project currently uses a local Windows Chrome installation/profile,
    # so we do not bundle a Chromium browser into the application.
    optional_data = collect_optional_data()

    # Use PyInstaller's Python API so this script works directly from
    # the same Python environment that passed Phase 14.7.
    import PyInstaller.__main__

    args = [
        str(ROOT / "main_ui.py"),

        "--name", APP_NAME,

        # Debug-friendly release layout.
        "--onedir",
        "--windowed",

        "--noconfirm",
        "--clean",

        "--distpath", str(DIST_DIR),
        "--workpath", str(BUILD_DIR),
        "--specpath", str(ROOT),

        # Make the LUNA root importable.
        "--paths", str(ROOT),

        # Packages with dynamic imports/data/native libraries.
        "--collect-all", "PySide6",
        "--collect-all", "faster_whisper",
        "--collect-all", "ctranslate2",
        "--collect-all", "av",
        "--collect-all", "edge_tts",
        "--collect-all", "pygame",
        "--collect-all", "playwright",
        "--collect-all", "sounddevice",

        # Runtime package metadata where relevant.
        "--copy-metadata", "faster-whisper",
        "--copy-metadata", "edge-tts",
        "--copy-metadata", "playwright",
    ]

    # Optional project asset folders.
    for source, destination in optional_data:
        args.extend([
            "--add-data",
            f"{source};{destination}",
        ])

    # Optional icon.
    icon_candidates = (
        ROOT / "logo.ico",
        ROOT / "assets" / "logo.ico",
        ROOT / "ui" / "logo.ico",
    )

    icon = next(
        (path for path in icon_candidates if path.is_file()),
        None,
    )

    if icon:
        args.extend([
            "--icon",
            str(icon),
        ])
        print(f"ICON: {icon}")
    else:
        print("ICON: not found; building without custom icon.")

    print()
    print("BUILD MODE: ONEDIR + WINDOWED")
    print("BUILDING...")
    print()

    try:
        PyInstaller.__main__.run(args)
    except SystemExit as error:
        code = int(error.code or 0)
        if code != 0:
            print(f"❌ PyInstaller exited with code {code}")
            return code
    except Exception as error:
        print(f"❌ Build failed: {error}")
        return 1

    exe = DIST_DIR / APP_NAME / f"{APP_NAME}.exe"

    print()
    print("=" * 78)

    if not exe.exists():
        print("❌ BUILD FAILED - LUNA.exe was not produced.")
        print("=" * 78)
        return 1

    print("✅ LUNA WINDOWS BUILD COMPLETE")
    print("=" * 78)
    print(f"EXECUTABLE: {exe}")
    print(f"RELEASE FOLDER: {exe.parent}")

    print()
    print("NEXT:")
    print(f'    "{exe}"')

    print()
    print("Keep the ONEDIR folder together when launching/distributing it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())