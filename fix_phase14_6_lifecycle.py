from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil

PROJECT = Path(r"C:\Users\shaik\Downloads\program\project\LUNA")
WINDOW = PROJECT / "ui" / "window.py"
BACKUP_ROOT = PROJECT / "backup_phase14_6"


def main() -> int:
    print("=" * 78)
    print("🌙 LUNA PHASE 14.6 - LIFECYCLE FIX")
    print("=" * 78)
    print(f"PROJECT ROOT: {PROJECT}")

    if not WINDOW.exists():
        print(f"❌ window.py not found: {WINDOW}")
        return 1

    source = WINDOW.read_text(encoding="utf-8")

    # Idempotent: do not duplicate shutdown code.
    if "self.agent.shutdown()" in source:
        print("✅ Agent shutdown already present in window.py")
        print("No modification required.")
        return 0

    close_marker = "        # Close browser\n\n        ActionExecutor.close_browser()\n"

    if close_marker not in source:
        print("❌ Expected closeEvent browser-cleanup block was not found.")
        print("No file was changed.")
        return 1

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    backup_dir = BACKUP_ROOT / timestamp
    backup_dir.mkdir(parents=True, exist_ok=True)

    backup_file = backup_dir / "window.py"
    shutil.copy2(WINDOW, backup_file)

    replacement = (
        "        # Close browser\n\n"
        "        ActionExecutor.close_browser()\n\n"
        "        # Close LUNA agent resources (browser worker + memory).\n"
        "        try:\n"
        "            self.agent.shutdown()\n"
        "        except Exception as error:\n"
        "            print(f\"[LUNA] Agent shutdown warning: {error}\")\n"
    )

    updated = source.replace(close_marker, replacement, 1)
    WINDOW.write_text(updated, encoding="utf-8")

    print(f"✅ Backup created at: {backup_file}")
    print("✅ Patched: ui/window.py")
    print()
    print("NEXT COMMAND:")
    print("python test_startup_shutdown_phase14_6.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())