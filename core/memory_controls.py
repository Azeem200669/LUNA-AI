"""LUNA Phase 12.5 - explicit memory controls.

Handles user-requested edits and deletion of long-term memories.
All mutations are explicit; normal conversation is not affected.
"""

from __future__ import annotations

import re
from typing import Optional


class MemoryControls:
    """Resolve and execute explicit memory update/forget commands."""

    def __init__(self, memory):
        self.memory = memory

    @staticmethod
    def _clean(value: str) -> str:
        value = re.sub(r"\s+", " ", (value or "").strip())
        return value.strip(" \t\r\n.,!?;:")

    @staticmethod
    def _slug(value: str) -> str:
        return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")

    @staticmethod
    def _type_for_subject(subject: str) -> str:
        s = subject.lower().strip()
        if "voice" in s or "favorite" in s or "preferred" in s or "language" in s:
            return "preference"
        if any(word in s for word in ("project", "game", "work")):
            return "project"
        if any(word in s for word in ("learn", "skill", "programming", "tool")):
            return "skill"
        if "goal" in s or "aim" in s or "plan" in s:
            return "goal"
        if "name" in s or "who am i" in s:
            return "profile"
        return "fact"

    @staticmethod
    def _candidate_keys(subject: str) -> list[str]:
        s = MemoryControls._clean(subject).lower()
        s = re.sub(r"^(?:my|the|current)\s+", "", s)
        slug = MemoryControls._slug(s)
        keys = []

        if "name" == slug:
            keys.append("name")
        if "voice" in slug:
            keys.extend(["preferred_voice", "voice"])
        if "language" in slug:
            keys.extend(["favorite_language", "preferred_language", "language"])
        if "project" in slug or "game" in slug or "work" in slug:
            keys.extend(["project_current", "project"])
        if "food" in slug:
            keys.extend(["preferred_food", "favorite_food"])
        if slug:
            keys.append(slug)
            keys.append("favorite_" + slug)
            keys.append("preferred_" + slug)
        return list(dict.fromkeys(keys))

    def _find_target(self, subject: str) -> Optional[dict]:
        for key in self._candidate_keys(subject):
            item = self.memory.get_memory(key)
            if item:
                return item

        query = self._clean(subject)
        if not query:
            return None

        results = self.memory.search(query, limit=20)
        if results:
            normalized = query.lower()
            exact = []
            for item in results:
                key = str(item.get("memory_key") or "").lower()
                value = str(item.get("memory_value") or "").lower()
                if normalized in key or normalized in value:
                    exact.append(item)
            if exact:
                return exact[0]

        return None

    def handle(self, message: str) -> Optional[str]:
        text = self._clean(message)
        if not text:
            return None

        lower = text.lower()

        # Never treat conversation-history commands as long-term-memory edits.
        if lower in {"clear this conversation", "clear conversation"}:
            return None

        # Explicitly erase every saved memory.
        if re.match(
            r"^(?:please\s+)?(?:forget|delete|remove|erase)\s+(?:everything|all(?: my)? memories|everything you remember about me)\.?$",
            lower,
        ):
            memories = self.memory.list_memories(limit=500)
            deleted = 0
            for item in memories:
                if self.memory.forget_memory(memory_id=item.get("id")):
                    deleted += 1
            return f"I forgot {deleted} saved memories."

        # Update/change/set an existing memory explicitly.
        update_match = re.match(
            r"^(?:please\s+)?(?:change|update|set|replace)\s+(?:my\s+)?(.+?)\s+(?:to|as)\s+(.+)$",
            text,
            flags=re.IGNORECASE,
        )
        if update_match:
            subject = self._clean(update_match.group(1))
            value = self._clean(update_match.group(2))
            if not subject or not value:
                return None

            target = self._find_target(subject)
            if target:
                key = str(target.get("memory_key") or "")
                if not key:
                    return None
                memory_type = str(target.get("memory_type") or "fact")
            else:
                key = self._candidate_keys(subject)[0] if self._candidate_keys(subject) else None
                if not key:
                    return None
                memory_type = self._type_for_subject(subject)

            self.memory.set_memory(
                key=key,
                value=value,
                memory_type=memory_type,
                source="explicit_user",
                confidence=1.0,
            )
            return f"Updated your {subject} memory to {value}."

        # Explicitly forget one memory.
        forget_match = re.match(
            r"^(?:please\s+)?(?:forget|delete|remove|erase)\s+(?:my\s+)?(.+)$",
            text,
            flags=re.IGNORECASE,
        )
        if forget_match:
            subject = self._clean(forget_match.group(1))
            if subject.lower() in {"this", "that"}:
                return None

            target = self._find_target(subject)
            if not target:
                return f"I couldn't find a saved memory matching '{subject}'."

            if self.memory.forget_memory(memory_id=target.get("id")):
                key = target.get("memory_key") or subject
                return f"I forgot the memory '{key}'."
            return "I couldn't remove that memory."

        return None