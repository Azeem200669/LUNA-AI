"""LUNA automatic memory extraction - Phase 12.3 fixed.

Rule-first, low-latency extraction for durable user-provided facts.
Explicit "remember" commands remain handled by LunaAgent separately.
"""

from __future__ import annotations

import re
from typing import Optional


class MemoryExtractor:
    """Extract useful long-term memories without an extra AI API call."""

    # The patterns are deliberately explicit so a phrase that should be
    # remembered cannot silently fall through because of a generic branch.
    PATTERNS = (
        # Goals
        ("goal", "goal", re.compile(
            r"^my\s+(?:goal|aim|plan)\s+is\s+(.{3,180})$",
            re.IGNORECASE,
        )),

        # Projects / current work
        ("project", "project", re.compile(
            r"^(?:i\s+am|i'm|i’m|i\s+am\s+currently|i'm\s+currently|i’m\s+currently)\s+"
            r"working\s+on\s+(.{3,180})$",
            re.IGNORECASE,
        )),
        ("project", "project", re.compile(
            r"^my\s+project\s+is\s+(.{3,180})$",
            re.IGNORECASE,
        )),
        ("project", "project", re.compile(
            r"^(?:i\s+am|i'm|i’m)\s+building\s+(.{3,180})$",
            re.IGNORECASE,
        )),

        # Likes / preferences
        ("preference", "preference", re.compile(
            r"^i\s+(?:like|love|prefer|enjoy)\s+(.{3,160})$",
            re.IGNORECASE,
        )),
        ("favorite", "preference", re.compile(
            r"^my\s+favorite\s+(.{2,80})\s+is\s+(.{2,120})$",
            re.IGNORECASE,
        )),
        ("preferred", "preference", re.compile(
            r"^my\s+preferred\s+(.{2,80})\s+is\s+(.{2,120})$",
            re.IGNORECASE,
        )),

        # Skills / tools
        ("skill", "skill", re.compile(
            r"^i\s+(?:use|work\s+with)\s+(.{2,120})$",
            re.IGNORECASE,
        )),
        ("skill", "skill", re.compile(
            r"^(?:i\s+am|i'm|i’m)\s+learning\s+(.{2,120})$",
            re.IGNORECASE,
        )),

        # Education
        ("education", "profile", re.compile(
            r"^(?:i\s+am|i'm|i’m)\s+(?:studying|a\s+student\s+of)\s+(.{2,160})$",
            re.IGNORECASE,
        )),

        # Name comes after more specific "I am ..." patterns so phrases
        # such as "I am learning Python" are not mistaken for names.
        ("name", "profile", re.compile(
            r"^(?:my\s+name\s+is|call\s+me|you\s+can\s+call\s+me|i\s+am|i\'m|i’m)\s+"
            r"([A-Za-z][A-Za-z .'-]{1,60})$",
            re.IGNORECASE,
        )),
    )

    def extract(self, text: str) -> Optional[dict]:
        """Return one extracted memory or None."""
        if not text:
            return None

        clean = self._clean(text)
        if not clean or self._looks_like_command(clean):
            return None

        for key, memory_type, pattern in self.PATTERNS:
            match = pattern.fullmatch(clean)
            if not match:
                continue

            # ----------------------------------------------------------
            # NAME
            # ----------------------------------------------------------
            if key == "name":
                value = self._clean_value(match.group(1))
                if not self._valid_name(value):
                    return None

                return {
                    "operation": "set_memory",
                    "key": "name",
                    "memory_type": "profile",
                    "value": value,
                    "confidence": 0.99,
                }

            # ----------------------------------------------------------
            # FAVORITE / PREFERRED
            # ----------------------------------------------------------
            if key in {"favorite", "preferred"}:
                subject = self._clean_value(match.group(1))
                value = self._clean_value(match.group(2))

                if not subject or not value:
                    return None

                prefix = "favorite_" if key == "favorite" else "preferred_"
                subject_slug = re.sub(
                    r"[^a-z0-9]+",
                    "_",
                    subject.lower(),
                ).strip("_")

                memory_key = prefix + subject_slug

                return {
                    "operation": "set_memory",
                    "key": memory_key,
                    "memory_type": "preference",
                    "value": value,
                    "confidence": 0.96,
                }

            # ----------------------------------------------------------
            # GENERIC / PROJECT / GOAL / SKILL / EDUCATION
            # ----------------------------------------------------------
            value = self._clean_value(match.group(1))
            if not value:
                return None

            if key == "project":
                memory_key = "project_current"
            else:
                slug = re.sub(
                    r"[^a-z0-9]+",
                    "_",
                    value.lower(),
                ).strip("_")[:55]
                memory_key = f"{key}_{slug}" if slug else None

            return {
                "operation": "set_memory" if memory_key else "remember",
                "key": memory_key,
                "memory_type": memory_type,
                "value": value,
                "confidence": 0.90,
            }

        return None

    @staticmethod
    def _clean(text: str) -> str:
        text = re.sub(
            r"^luna\s*[,;:]?\s*",
            "",
            text.strip(),
            flags=re.IGNORECASE,
        )
        return re.sub(r"\s+", " ", text).strip().strip(" \t\r\n.!?;")

    @staticmethod
    def _clean_value(value: str) -> str:
        return re.sub(r"\s+", " ", value.strip()).strip(
            " \t\r\n.,!?;:"
        )

    @staticmethod
    def _valid_name(value: str) -> bool:
        if not value or len(value) > 60:
            return False

        blocked = {
            "hungry",
            "tired",
            "busy",
            "happy",
            "sad",
            "working",
            "learning",
            "studying",
            "building",
        }

        return (
            value.lower() not in blocked
            and 1 <= len(value.split()) <= 5
        )

    @staticmethod
    def _looks_like_command(text: str) -> bool:
        lower = text.lower()

        command_prefixes = (
            "open ",
            "close ",
            "go to ",
            "search ",
            "find ",
            "take a screenshot",
            "show me ",
            "increase ",
            "decrease ",
            "mute",
            "unmute",
            "press ",
            "type ",
            "click ",
            "remember ",
            "forget ",
        )

        return lower.startswith(command_prefixes)

    def save(self, memory_manager, text: str) -> Optional[dict]:
        """Extract and persist one memory."""
        result = self.extract(text)

        if not result:
            return None

        if result["operation"] == "set_memory":
            memory_manager.set_memory(
                key=result["key"],
                value=result["value"],
                memory_type=result["memory_type"],
                source="auto_extracted",
                confidence=result["confidence"],
            )
        else:
            memory_manager.remember(
                value=result["value"],
                memory_type=result["memory_type"],
                source="auto_extracted",
                confidence=result["confidence"],
            )

        return result