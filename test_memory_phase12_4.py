"""LUNA Phase 12.4 - intelligent memory retrieval test."""

from __future__ import annotations

import tempfile
from pathlib import Path

from core.memory import MemoryManager
from core.memory_retriever import MemoryRetriever


def _keys(items):
    return [str(item.get("memory_key")) for item in items]


def main() -> int:
    print("=" * 78)
    print("🌙 LUNA PHASE 12.4 - INTELLIGENT MEMORY RETRIEVAL TEST")
    print("=" * 78)

    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "memory.db"
        memory = MemoryManager(db_path)

        try:
            # Same memories produced by Phase 12.3, plus a few unrelated ones.
            memory.set_memory(
                "goal_luna_assistant",
                "build LUNA into a complete personal AI assistant",
                memory_type="goal",
                confidence=0.95,
            )
            memory.set_memory(
                "project_current",
                "an anime card game",
                memory_type="project",
                confidence=0.9,
            )
            memory.set_memory(
                "preference_anime_games",
                "anime games",
                memory_type="preference",
                confidence=0.9,
            )
            memory.set_memory(
                "favorite_language",
                "Python",
                memory_type="preference",
                confidence=0.96,
            )
            memory.set_memory(
                "preferred_voice",
                "Microsoft Zira",
                memory_type="preference",
                confidence=0.96,
            )
            memory.set_memory(
                "skill_python",
                "Python",
                memory_type="skill",
                confidence=0.9,
            )
            memory.set_memory(
                "favorite_color",
                "blue",
                memory_type="preference",
                confidence=1.0,
            )
            memory.set_memory(
                "preferred_food",
                "biryani",
                memory_type="preference",
                confidence=1.0,
            )

            retriever = MemoryRetriever(memory)

            cases = [
                (
                    "What game am I working on?",
                    "project_current",
                    "anime card game",
                ),
                (
                    "What programming language am I learning?",
                    "skill_python",
                    "Python",
                ),
                (
                    "What is my preferred voice?",
                    "preferred_voice",
                    "Microsoft Zira",
                ),
                (
                    "What is my name?",
                    None,
                    None,
                ),
            ]

            # Add identity only for the name-specific test.
            memory.set_memory(
                "name",
                "Shaik",
                memory_type="profile",
                confidence=1.0,
            )

            for index, (query, expected_key, expected_value) in enumerate(cases, start=1):
                print()
                print("=" * 78)
                print(f"TEST {index}: {query}")
                print("=" * 78)

                results = retriever.retrieve(query)
                keys = _keys(results)

                print("RETRIEVED:")
                for item in results:
                    print(
                        f"- {item.get('memory_key')} -> "
                        f"{item.get('memory_value')} "
                        f"[score={item.get('relevance_score')}]"
                    )

                if expected_key is not None:
                    assert expected_key in keys, (
                        f"Expected {expected_key}, got {keys}"
                    )
                    assert keys[0] == expected_key, (
                        f"Expected top result {expected_key}, got {keys}"
                    )
                    match = next(item for item in results if item.get("memory_key") == expected_key)
                    assert expected_value.lower() in str(match.get("memory_value", "")).lower()
                else:
                    assert "name" in keys, f"Expected name memory, got {keys}"

                if expected_key == "preferred_voice":
                    assert "preferred_food" not in keys, (
                        f"Unrelated preference was retrieved: {keys}"
                    )

                print("PASS")

            print()
            print("=" * 78)
            print("TEST 5: unrelated query should not retrieve unrelated memories")
            print("=" * 78)
            unrelated = retriever.retrieve("What is the weather forecast?")
            print("RETRIEVED KEYS:", _keys(unrelated))
            assert unrelated == [], f"Unexpected memories: {_keys(unrelated)}"
            print("PASS")

            print()
            print("=" * 78)
            print("✅ PHASE 12.4 PASSED")
            print("=" * 78)
            return 0

        finally:
            memory.close()


if __name__ == "__main__":
    raise SystemExit(main())