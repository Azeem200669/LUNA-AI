"""LUNA Phase 12.2 - explicit memory + identity + persistence test."""

from __future__ import annotations

import tempfile
from pathlib import Path

from core.agent import LunaAgent
from core.memory import MemoryManager


def main() -> int:
    print("=" * 78)
    print("🌙 LUNA PHASE 12.2 - MEMORY INTEGRATION TEST")
    print("=" * 78)

    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "luna_memory_test.db"

        agent = LunaAgent()

        # Replace production DB with isolated test DB.
        try:
            agent.memory.close()
        except Exception:
            pass
        agent.memory = MemoryManager(db_path)
        agent.session_id = "phase12-2-test"

        try:
            # --------------------------------------------------------
            # 1. Name
            # --------------------------------------------------------
            print("\n" + "=" * 78)
            print("TEST 1: Remember Name")
            print("=" * 78)

            response = agent.chat("My name is Shaik.")
            print("LUNA:", response)

            assert agent.memory.get_name() == "Shaik"
            print("PASS: Name saved.")

            # --------------------------------------------------------
            # 2. Generic memory
            # --------------------------------------------------------
            print("\n" + "=" * 78)
            print("TEST 2: Remember Generic Fact")
            print("=" * 78)

            response = agent.chat(
                "Remember that I am building LUNA as my personal AI assistant."
            )
            print("LUNA:", response)

            results = agent.memory.search("building LUNA")
            assert results
            print("PASS: Generic fact saved.")

            # --------------------------------------------------------
            # 3. Preference
            # --------------------------------------------------------
            print("\n" + "=" * 78)
            print("TEST 3: Remember Preference")
            print("=" * 78)

            response = agent.chat(
                "Remember my favorite language is Python."
            )
            print("LUNA:", response)

            results = agent.memory.search("favorite language")
            assert results
            assert results[0]["memory_type"] == "preference"
            print("PASS: Preference saved with type=preference.")

            # --------------------------------------------------------
            # 4. Query name
            # --------------------------------------------------------
            print("\n" + "=" * 78)
            print("TEST 4: Recall Name")
            print("=" * 78)

            response = agent.chat("What is my name?")
            print("LUNA:", response)

            assert "Shaik" in response
            print("PASS: Name recalled.")

            # --------------------------------------------------------
            # 5. Query all memory
            # --------------------------------------------------------
            print("\n" + "=" * 78)
            print("TEST 5: List Saved Memories")
            print("=" * 78)

            response = agent.chat("What do you remember about me?")
            print("LUNA:")
            print(response)

            assert "name" in response.lower()
            assert "python" in response.lower()
            print("PASS: Saved memories listed.")

            # --------------------------------------------------------
            # 6. Conversation persistence
            # --------------------------------------------------------
            print("\n" + "=" * 78)
            print("TEST 6: Conversation History")
            print("=" * 78)

            history = agent.memory.get_recent_messages(
                agent.session_id,
                limit=20,
            )

            assert len(history) >= 10
            print(f"PASS: {len(history)} messages stored.")

            # --------------------------------------------------------
            # 7. Stats
            # --------------------------------------------------------
            print("\n" + "=" * 78)
            print("TEST 7: Statistics")
            print("=" * 78)

            stats = agent.memory.stats()
            print("Memories:", stats["memories"])
            print("Conversation messages:", stats["conversation_messages"])

            assert stats["memories"] >= 3
            assert stats["conversation_messages"] >= 10
            print("PASS: Statistics correct.")

        finally:
            agent.shutdown()

    print("\n" + "=" * 78)
    print("✅ PHASE 12.2 PASSED")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())