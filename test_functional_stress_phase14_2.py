"""LUNA Phase 14.2 - local functional stress test.

No GUI, microphone, browser, Groq call, or Windows action is launched.
Exercises local routing, memory, retrieval, memory controls, STOP generation
guards, and barge-in command logic repeatedly and concurrently.
"""

from __future__ import annotations

import tempfile
import threading
from pathlib import Path

from core.barge_in import BargeInListener
from core.fast_router import FastRouter
from core.memory import MemoryManager
from core.memory_controls import MemoryControls
from core.memory_extractor import MemoryExtractor
from core.memory_retriever import MemoryRetriever
from core.stop_control import GenerationGuard


def main() -> int:
    print("=" * 78)
    print("🌙 LUNA PHASE 14.2 - LOCAL FUNCTIONAL STRESS TEST")
    print("=" * 78)

    # TEST 1: FastRouter repeated routing
    print("\nTEST 1: FastRouter repeated routing")
    router = FastRouter()

    route_cases = (
        ("Luna, open Calculator", "computer"),
        ("Luna, take a screenshot", "computer"),
        ("Luna, increase volume", "computer"),
        ("Luna, open YouTube", "browser"),
        ("Luna, search YouTube for AI tutorials", "browser"),
        ("Luna, search for Python tutorials", "web"),
        ("Luna, find agent.py", "file"),
        ("Luna, show files in my LUNA project", "file"),
        ("Explain machine learning", "ai"),
        ("What is Python?", "ai"),
    )

    total_routes = 0
    for _ in range(200):
        for message, expected in route_cases:
            result = router.route(message)
            if isinstance(result, str):
                actual = result.strip().lower()
            elif isinstance(result, dict):
                actual = str(
                    result.get("route")
                    or result.get("category")
                    or result.get("type")
                    or result.get("name")
                    or result.get("intent")
                    or "ai"
                ).strip().lower()
            else:
                actual = "ai"

            assert actual == expected, (
                f"Route mismatch: {message!r} -> {actual!r}, "
                f"expected {expected!r}"
            )
            total_routes += 1

    print(f"ROUTED: {total_routes}")
    print("PASS")

    # TEST 2: Automatic memory extraction repeated
    print("\nTEST 2: automatic memory extraction repeated")
    extractor = MemoryExtractor()

    extraction_cases = (
        ("My goal is to build LUNA into a complete personal AI assistant.", "goal"),
        ("I am working on an anime card game.", "project"),
        ("I like anime games.", "preference"),
        ("My favorite language is Python.", "preference"),
        ("My preferred voice is Microsoft Zira.", "preference"),
        ("I am learning Python.", "skill"),
    )

    for _ in range(50):
        for message, expected_type in extraction_cases:
            result = extractor.extract(message)
            assert result is not None, message
            assert result["memory_type"] == expected_type, result

    print("EXTRACTIONS:", len(extraction_cases) * 50)
    print("PASS")

    # TEST 3: Persistence + retrieval + memory controls
    print("\nTEST 3: memory persistence / retrieval / controls")
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "memory.db"
        memory = MemoryManager(db_path)

        try:
            memory.set_memory(
                "project_current", "an anime card game",
                memory_type="project", confidence=0.9
            )
            memory.set_memory(
                "favorite_language", "Python",
                memory_type="preference", confidence=0.96
            )
            memory.set_memory(
                "preferred_voice", "Microsoft Zira",
                memory_type="preference", confidence=0.96
            )
            memory.set_memory(
                "skill_python", "Python",
                memory_type="skill", confidence=0.9
            )
            memory.set_memory(
                "name", "Shaik",
                memory_type="profile", confidence=1.0
            )

            retriever = MemoryRetriever(memory)
            controls = MemoryControls(memory)

            assert retriever.retrieve(
                "What game am I working on?"
            )[0]["memory_key"] == "project_current"

            assert retriever.retrieve(
                "What programming language am I learning?"
            )[0]["memory_key"] == "skill_python"

            assert retriever.retrieve(
                "What is my preferred voice?"
            )[0]["memory_key"] == "preferred_voice"

            assert retriever.retrieve(
                "What is my name?"
            )[0]["memory_key"] == "name"

            assert controls.handle(
                "update my favorite language to Java"
            ) is not None
            assert memory.get_memory(
                "favorite_language"
            )["memory_value"] == "Java"

            assert controls.handle(
                "forget my preferred voice"
            ) is not None
            assert memory.get_memory("preferred_voice") is None

            memory.close()
            memory = MemoryManager(db_path)

            assert memory.get_memory(
                "favorite_language"
            )["memory_value"] == "Java"
            assert memory.get_memory("project_current") is not None
            assert memory.get_memory("name") is not None

        finally:
            memory.close()

    print("PERSISTENCE: PASS")
    print("RETRIEVAL: PASS")
    print("CONTROLS: PASS")
    print("PASS")

    # TEST 4: Concurrent SQLite access
    print("\nTEST 4: concurrent memory read/write stress")
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "memory_concurrent.db"
        memory = MemoryManager(db_path)

        errors: list[BaseException] = []
        errors_lock = threading.Lock()

        def worker(index: int) -> None:
            try:
                for iteration in range(25):
                    key = f"stress_{index}_{iteration}"
                    memory.set_memory(
                        key,
                        f"value {index}-{iteration}",
                        memory_type="stress",
                        confidence=1.0,
                    )
                    assert memory.get_memory(key) is not None
                    memory.search(str(index), limit=5)
                    memory.list_memories(limit=5)
            except BaseException as error:
                with errors_lock:
                    errors.append(error)

        threads = [
            threading.Thread(
                target=worker,
                args=(index,),
                name=f"LUNA-Memory-Stress-{index}",
            )
            for index in range(12)
        ]

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert not errors, f"Concurrent memory errors: {errors}"
        assert memory.stats()["memories"] == 300
        memory.close()

    print("THREADS: 12")
    print("WRITES: 300")
    print("PASS")

    # TEST 5: GenerationGuard concurrency
    print("\nTEST 5: STOP generation concurrency")
    guard = GenerationGuard()
    tokens: list[int] = []
    token_lock = threading.Lock()

    def generation_worker() -> None:
        token = guard.next()
        with token_lock:
            tokens.append(token)

    threads = [
        threading.Thread(
            target=generation_worker,
            name=f"LUNA-Generation-{index}",
        )
        for index in range(100)
    ]

    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(tokens) == 100
    assert len(set(tokens)) == 100

    current = guard.current()
    assert current in tokens
    assert guard.is_current(current)

    old_token = current
    invalidated = guard.invalidate()
    assert invalidated > old_token
    assert not guard.is_current(old_token)
    assert guard.is_current(invalidated)

    print("GENERATION TOKENS:", len(tokens))
    print("PASS")

    # TEST 6: Barge-in command stress
    print("\nTEST 6: voice STOP phrase stress")
    positive = (
        "stop",
        "please stop",
        "stop Luna",
        "stop speaking",
        "cancel",
        "cancel Luna",
        "stop it",
        "be quiet",
        "quiet",
        "that's enough",
        "thats enough",
        "enough",
    )
    negative = (
        "tell me about Python",
        "open Chrome",
        "what is machine learning",
        "I am learning Python",
        "stopwatch",
        "cancelled order",
    )

    for _ in range(200):
        for phrase in positive:
            assert BargeInListener.is_stop_command(phrase), phrase
        for phrase in negative:
            assert not BargeInListener.is_stop_command(phrase), phrase

    print("POSITIVE CHECKS:", len(positive) * 200)
    print("NEGATIVE CHECKS:", len(negative) * 200)
    print("PASS")

    # TEST 7: Extraction -> save -> retrieval
    print("\nTEST 7: extraction → save → retrieval pipeline")
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "memory_pipeline.db"
        memory = MemoryManager(db_path)

        try:
            messages = (
                "My goal is to build LUNA into a complete personal AI assistant.",
                "I am working on an anime card game.",
                "I like anime games.",
                "My favorite language is Python.",
                "My preferred voice is Microsoft Zira.",
                "I am learning Python.",
            )

            for message in messages:
                assert extractor.save(memory, message) is not None

            retriever = MemoryRetriever(memory)

            assert retriever.retrieve(
                "Tell me about the game I am building."
            )[0]["memory_key"] == "project_current"

            assert retriever.retrieve(
                "What language am I learning?"
            )[0]["memory_key"] == "skill_python"

            assert retriever.retrieve(
                "Which voice do I prefer?"
            )[0]["memory_key"] == "preferred_voice"

            assert retriever.retrieve(
                "Something completely unrelated to my memories"
            ) == []

        finally:
            memory.close()

    print("PIPELINE CASES: 4")
    print("PASS")

    print("\n" + "=" * 78)
    print("✅ PHASE 14.2 LOCAL FUNCTIONAL STRESS PASSED")
    print("=" * 78)
    print("NOTE: No GUI, microphone, browser, Windows action, or live AI API was launched.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())