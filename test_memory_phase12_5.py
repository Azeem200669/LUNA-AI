"""LUNA Phase 12.5 - explicit memory controls test."""

from __future__ import annotations

import tempfile
from pathlib import Path

from core.memory import MemoryManager
from core.memory_controls import MemoryControls


def main() -> int:
    print("=" * 78)
    print("🌙 LUNA PHASE 12.5 - MEMORY CONTROLS TEST")
    print("=" * 78)

    with tempfile.TemporaryDirectory() as temp_dir:
        memory = MemoryManager(Path(temp_dir) / "memory.db")
        try:
            memory.set_name("Shaik")
            memory.set_memory("preferred_voice", "Microsoft Zira", "preference")
            memory.set_memory("favorite_language", "Python", "preference")
            memory.set_memory("project_current", "an anime card game", "project")
            memory.set_memory("goal_luna", "build LUNA into a personal AI assistant", "goal")

            controls = MemoryControls(memory)

            tests = [
                ("forget my preferred voice", "preferred_voice"),
                ("update my favorite language to Java", "favorite_language"),
                ("forget my anime card game", "project_current"),
                ("forget my name", "name"),
            ]

            for index, (command, expected_key) in enumerate(tests, start=1):
                print()
                print("=" * 78)
                print(f"TEST {index}: {command}")
                print("EXPECTED KEY: " + expected_key)
                print("=" * 78)

                response = controls.handle(command)
                print("RESPONSE:", response)
                assert response is not None

                if command.startswith("update"):
                    item = memory.get_memory(expected_key)
                    assert item and item["memory_value"] == "Java", item
                else:
                    assert memory.get_memory(expected_key) is None

                print("PASS")

            print()
            print("=" * 78)
            print("TEST 5: forget everything you remember about me")
            print("=" * 78)
            response = controls.handle("forget everything you remember about me")
            print("RESPONSE:", response)
            assert response is not None
            assert memory.list_memories(limit=100) == []
            print("PASS")

            print()
            print("=" * 78)
            print("TEST 6: unrelated command is ignored")
            print("=" * 78)
            response = controls.handle("open Chrome")
            print("RESPONSE:", response)
            assert response is None
            print("PASS")

            print()
            print("=" * 78)
            print("✅ PHASE 12.5 PASSED")
            print("=" * 78)
            return 0
        finally:
            memory.close()


if __name__ == "__main__":
    raise SystemExit(main())