"""LUNA Phase 12.3 - automatic memory extraction test (Windows-safe cleanup)."""

from __future__ import annotations

import tempfile
from pathlib import Path

from core.memory import MemoryManager
from core.memory_extractor import MemoryExtractor


def main() -> int:
    print("=" * 78)
    print("🌙 LUNA PHASE 12.3 - AUTOMATIC MEMORY EXTRACTION TEST")
    print("=" * 78)

    # IMPORTANT: close MemoryManager BEFORE TemporaryDirectory cleans up.
    # On Windows an open SQLite connection keeps memory.db locked.
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "memory.db"
        memory = MemoryManager(db_path)

        try:
            extractor = MemoryExtractor()

            cases = [
                ("My goal is to build LUNA into a complete personal AI assistant.", "goal"),
                ("I am working on an anime card game.", "project"),
                ("I like anime games.", "preference"),
                ("My favorite language is Python.", "preference"),
                ("My preferred voice is Microsoft Zira.", "preference"),
                ("I am learning Python.", "skill"),
            ]

            for index, (message, expected_type) in enumerate(cases, start=1):
                print()
                print("=" * 78)
                print(f"TEST {index}: {message}")
                print("EXPECTED TYPE: " + expected_type)
                print("=" * 78)

                result = extractor.save(memory, message)

                assert result is not None, f"No extraction for: {message}"
                assert result["memory_type"] == expected_type, result

                print("EXTRACTED:", result)
                print("PASS")

            assert memory.get_memory("favorite_language") is not None
            assert memory.get_memory("preferred_voice") is not None
            assert memory.get_memory("project_current") is not None

            print()
            print("=" * 78)
            print("SAVED MEMORIES")
            print("=" * 78)

            for item in memory.list_memories(limit=20):
                print(
                    f"- {item['memory_type']}: "
                    f"{item.get('memory_key')} -> "
                    f"{item['memory_value']}"
                )

            print()
            print("=" * 78)
            print("✅ PHASE 12.3 PASSED")
            print("=" * 78)
            return 0

        finally:
            # This MUST happen before TemporaryDirectory.__exit__().
            memory.close()


if __name__ == "__main__":
    raise SystemExit(main())