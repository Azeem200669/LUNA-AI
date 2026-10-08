"""LUNA Phase 12.4 - intelligent long-term memory retrieval.

Ranks saved memories against the current user request so LUNA only sends
relevant memories to the AI model instead of dumping the whole memory store.
"""

from __future__ import annotations

import math
import re
from datetime import datetime, timezone
from typing import Any, Iterable, Optional


class MemoryRetriever:
    """Lightweight, local relevance ranking for LUNA's saved memories.

    The retriever intentionally uses the existing MemoryManager API, so it
    does not create another SQLite connection and remains safe with the
    thread-safe MemoryManager already used by LunaAgent.
    """

    STOPWORDS = {
        "a", "an", "and", "am", "are", "as", "at", "be", "but", "by",
        "can", "could", "did", "do", "does", "for", "from", "how", "i",
        "in", "is", "it", "me", "my", "of", "on", "or", "that", "the",
        "this", "to", "was", "what", "when", "where", "which", "who",
        "why", "will", "with", "would", "you", "your", "have", "has",
        "had", "tell", "remember", "know", "about", "currently", "today",
    }

    TYPE_HINTS = {
        "profile": {
            "name", "called", "call", "identity",
        },
        "project": {
            "project", "working", "build", "building", "game", "games",
            "app", "application", "develop", "developing", "create",
            "creating", "work",
        },
        "skill": {
            "learn", "learning", "study", "studying", "skill", "skills",
            "practice", "practicing", "programming", "code", "coding",
        },
        "preference": {
            "like", "likes", "love", "favorite", "favourite", "prefer",
            "preferred", "preference", "voice", "theme", "style",
            "language",
        },
        "goal": {
            "goal", "goals", "aim", "aims", "objective", "objectives",
            "dream", "plan", "plans", "want", "wants", "purpose",
        },
    }

    STRONG_INTENT_HINTS = {
        "profile": {"name", "called", "call", "identity"},
        "project": {
            "project", "working", "build", "building", "game", "games",
            "develop", "developing", "create", "creating", "work",
        },
        "skill": {
            "learn", "learning", "study", "studying", "skill", "skills",
            "practice", "practicing", "programming", "coding", "code",
        },
        "preference": {
            "like", "likes", "love", "favorite", "favourite", "prefer",
            "preferred", "preference", "voice", "theme", "style",
        },
        "goal": {
            "goal", "goals", "aim", "aims", "objective", "objectives",
            "dream", "plan", "plans", "purpose",
        },
    }

    TOPIC_TERMS = {
        "voice": {"voice", "tts", "speech", "speaker"},
        "language": {"language", "languages"},
    }

    TOKEN_RE = re.compile(r"[a-z0-9_]+", re.IGNORECASE)

    def __init__(self, memory_manager):
        self.memory = memory_manager

    @classmethod
    def _tokens(cls, text: str, *, remove_stopwords: bool = True) -> list[str]:
        # Treat memory keys such as ``preferred_voice`` and ``skill_python``
        # as separate semantic words.
        clean_text = (text or "").replace("_", " ")
        tokens = [token.lower() for token in cls.TOKEN_RE.findall(clean_text)]
        if remove_stopwords:
            tokens = [token for token in tokens if token not in cls.STOPWORDS]
        return tokens

    @staticmethod
    def _normalise_text(text: str) -> str:
        return " ".join((text or "").lower().split())

    @classmethod
    def _type_hints_for_query(cls, tokens: Iterable[str]) -> set[str]:
        token_set = set(tokens)
        hints: set[str] = set()
        for memory_type, words in cls.TYPE_HINTS.items():
            if token_set.intersection(words):
                hints.add(memory_type)
        return hints

    @staticmethod
    def _recency_bonus(updated_at: Optional[str]) -> float:
        if not updated_at:
            return 0.0
        try:
            stamp = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
            if stamp.tzinfo is None:
                stamp = stamp.replace(tzinfo=timezone.utc)
            age_days = max(
                0.0,
                (datetime.now(timezone.utc) - stamp).total_seconds() / 86400.0,
            )
            # Small bonus only. Relevance should dominate recency.
            return max(0.0, 1.0 - math.log1p(age_days) / 8.0)
        except Exception:
            return 0.0

    def _score_memory(self, query: str, item: dict[str, Any]) -> tuple[float, list[str]]:
        query_tokens = self._tokens(query)
        if not query_tokens:
            return 0.0, []

        key = str(item.get("memory_key") or "")
        value = str(item.get("memory_value") or "")
        memory_type = str(item.get("memory_type") or "fact").lower()

        key_tokens = set(self._tokens(key))
        value_tokens = set(self._tokens(value))
        all_text_tokens = key_tokens | value_tokens
        query_set = set(query_tokens)
        hints = self._type_hints_for_query(query_tokens)
        strong_hints = {
            memory_type
            for memory_type, words in self.STRONG_INTENT_HINTS.items()
            if query_set.intersection(words)
        }

        score = 0.0
        reasons: list[str] = []

        # Strong key match: memory keys are deliberately stable identifiers.
        key_overlap = query_set.intersection(key_tokens)
        if key_overlap:
            score += 4.0 * len(key_overlap)
            reasons.append("key-match")

        # Value match: useful for things such as "anime game" or "Python".
        value_overlap = query_set.intersection(value_tokens)
        if value_overlap:
            score += 4.0 * len(value_overlap)
            reasons.append("value-match")

        # Direct phrase match is stronger than isolated token overlap.
        query_norm = self._normalise_text(query)
        key_norm = self._normalise_text(key)
        value_norm = self._normalise_text(value)
        if len(query_norm) >= 4 and query_norm in value_norm:
            score += 6.0
            reasons.append("phrase-match")
        elif len(query_norm) >= 4 and query_norm in key_norm:
            score += 6.0
            reasons.append("phrase-key-match")

        # Intent/type match and mismatch. Strong intents (for example
        # "learning" -> skill) dominate generic terms such as "language".
        if memory_type in strong_hints:
            score += 5.0
            reasons.append("strong-type-match")
        elif strong_hints:
            score -= 4.5
            reasons.append("strong-type-mismatch")
        elif memory_type in hints:
            score += 2.0
            reasons.append("type-match")

        # A specific topic such as "voice" should not retrieve every
        # preference. Require a topical connection unless this is a broad
        # preference query.
        for topic, words in self.TOPIC_TERMS.items():
            if query_set.intersection(words):
                topic_overlap = query_set.intersection(words) & (key_tokens | value_tokens)
                if topic_overlap:
                    # "learning a language" is a skill request; the user's
                    # favorite language is related but should not outrank the
                    # actual learning/skill memory.
                    if (
                        topic == "language"
                        and memory_type == "preference"
                        and "skill" in strong_hints
                        and "preference" not in strong_hints
                    ):
                        score -= 3.0
                        reasons.append("topic-language-skill-filter")
                    else:
                        score += 3.0
                        reasons.append(f"topic-{topic}")
                elif strong_hints:
                    # A specific preference topic should not pull every
                    # memory of the same broad type. For example,
                    # "favorite language" should not return the preferred
                    # voice unless the memory itself mentions language.
                    if memory_type == "preference":
                        score -= 8.0

        # Confidence and recency are tie-breakers, never the main signal.
        confidence = max(0.0, min(1.0, float(item.get("confidence", 1.0))))
        score += confidence * 2.0
        score += self._recency_bonus(item.get("updated_at"))

        # Keys like "project_current" imply the type even when the type is
        # absent or user-created with an unusual category.
        if memory_type not in hints and any(
            marker in key.lower() for marker in ("project", "goal", "skill", "preference", "name")
        ):
            marker_map = {
                "project": "project",
                "goal": "goal",
                "skill": "skill",
                "preference": "preference",
                "name": "profile",
            }
            for marker, mapped_type in marker_map.items():
                if marker in key.lower() and mapped_type in hints:
                    score += 2.5
                    reasons.append("key-type-hint")
                    break

        # If there is absolutely no lexical connection and no intent match,
        # keep the item below retrieval threshold.
        if not key_overlap and not value_overlap and not hints:
            score -= 3.0

        return score, reasons

    def retrieve(
        self,
        query: str,
        limit: int = 6,
        candidate_limit: int = 500,
        min_score: float = 4.5,
    ) -> list[dict[str, Any]]:
        """Return the most relevant active memories for ``query``.

        The returned dictionaries preserve the MemoryManager fields and add
        ``relevance_score`` and ``relevance_reasons`` for diagnostics/tests.
        """
        query = (query or "").strip()
        if not query:
            return []

        limit = max(1, min(int(limit), 20))
        candidate_limit = max(1, min(int(candidate_limit), 500))

        candidates = self.memory.list_memories(limit=candidate_limit)
        ranked: list[dict[str, Any]] = []

        for item in candidates:
            score, reasons = self._score_memory(query, item)
            if score < min_score:
                continue

            enriched = dict(item)
            enriched["relevance_score"] = round(score, 3)
            enriched["relevance_reasons"] = reasons
            ranked.append(enriched)

        ranked.sort(
            key=lambda item: (
                float(item.get("relevance_score", 0.0)),
                float(item.get("confidence", 0.0)),
                str(item.get("updated_at", "")),
            ),
            reverse=True,
        )

        return ranked[:limit]