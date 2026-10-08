"""LUNA Phase 13.2 - thread-safe generation tokens for STOP race handling."""
from __future__ import annotations

import threading


class GenerationGuard:
    """Monotonic, thread-safe generation counter.

    Every new operation captures a generation token. STOP invalidates the
    previous token by advancing the counter. Late callbacks can then check
    whether their token is still current before touching the UI/audio state.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._generation = 0

    def next(self) -> int:
        with self._lock:
            self._generation += 1
            return self._generation

    def current(self) -> int:
        with self._lock:
            return self._generation

    def is_current(self, token: int) -> bool:
        with self._lock:
            return int(token) == self._generation

    def invalidate(self) -> int:
        return self.next()