from nlp.language_detector import LanguageDetector
from nlp.intent_classifier import IntentClassifier
from nlp.entity_extractor import EntityExtractor
from nlp.semantic_parser import MultilingualSemanticParser


class NLPEngine:

    def __init__(self):

        self.semantic_parser = (
            MultilingualSemanticParser()
        )

    # ========================================================
    # ANALYZE
    # ========================================================

    def analyze(
        self,
        text: str
    ):

        if not text:

            return {
                "language": "en",
                "language_name": "English",
                "intent": "unknown",
                "entity": None,
                "text": None,
                "key": None,
                "x": None,
                "y": None,
                "is_command": False,
                "confidence": 0.0,
                "source": "none",
            }

        # ====================================================
        # LANGUAGE
        # ====================================================

        language = (
            LanguageDetector.detect(
                text
            )
        )

        # ====================================================
        # FAST LOCAL NLP
        # ====================================================

        local_intent = (
            IntentClassifier.classify(
                text
            )
        )

        local_entity = None

        if local_intent == "open_application":

            local_entity = (
                EntityExtractor.find_application(
                    text
                )
            )

        elif local_intent == "open_website":

            local_entity = (
                EntityExtractor.find_website(
                    text
                )
            )

        elif local_intent == "open_folder":

            local_entity = (
                EntityExtractor.find_folder(
                    text
                )
            )

        elif local_intent == "type_text":

            local_entity = (
                EntityExtractor.find_typed_text(
                    text
                )
            )

        elif local_intent == "press_key":

            local_entity = (
                EntityExtractor.find_key(
                    text
                )
            )

        # ====================================================
        # FAST RESULT
        # ====================================================

        if (
            local_intent != "unknown"
            and (
                local_intent
                not in [
                    "open_application",
                    "open_website",
                    "open_folder",
                ]
                or local_entity
            )
        ):

            return {

                "language": language,

                "language_name":
                    LanguageDetector.name(
                        language
                    ),

                "intent": local_intent,

                "entity": local_entity,

                "text":
                    local_entity
                    if local_intent == "type_text"
                    else None,

                "key":
                    local_entity
                    if local_intent == "press_key"
                    else None,

                "x": None,

                "y": None,

                "is_command": True,

                "confidence": 0.99,

                "source": "local",
            }

        # ====================================================
        # MULTILINGUAL SEMANTIC PARSER
        # ====================================================

        print(
            "[NLP] Local rules did not fully understand "
            "the command."
        )

        print(
            "[NLP] Using multilingual semantic parser..."
        )

        semantic = (
            self.semantic_parser.parse(
                text
            )
        )

        # ====================================================
        # SEMANTIC RESULT
        # ====================================================

        intent = semantic.get(
            "intent",
            "unknown"
        )

        target = semantic.get(
            "target"
        )

        typed_text = semantic.get(
            "text"
        )

        key = semantic.get(
            "key"
        )

        x = semantic.get(
            "x"
        )

        y = semantic.get(
            "y"
        )

        confidence = float(
            semantic.get(
                "confidence",
                0.0
            )
        )

        is_command = (
            intent != "unknown"
            and confidence >= 0.60
        )

        return {

            "language": language,

            "language_name":
                LanguageDetector.name(
                    language
                ),

            "intent": intent,

            "entity": target,

            "text": typed_text,

            "key": key,

            "x": x,

            "y": y,

            "is_command": is_command,

            "confidence": confidence,

            "source": "semantic",
        }


# ============================================================
# ============================================================
#
#   🌙 LUNA NLP ENGINE PRO — EXTENSIONS (APPEND ONLY)
#
#   The original NLPEngine above is 100% unchanged.
#   Pro keeps the exact result schema (same keys, same
#   values) and fixes the wiring between the Pro
#   classifier/extractor and the engine:
#
#   FIXES
#     • New intents returned with entity: None —
#       "close chrome", "play lofi on youtube",
#       "set volume to 40", "remind me in 10 minutes"
#       all classified fine (via IntentClassifierPro)
#       but the engine extracted NOTHING for them,
#       producing executable-looking results with no
#       target. Pro extracts entities for every
#       entity-requiring intent.
#     • No validation for the new intents — the base
#       early-exit only required entities for the three
#       open_* intents. Pro extends the required-entity
#       set, so "open the thing" (app unknown) still
#       falls through to the semantic parser.
#     • "youtube lofi" / "google weather" opened the
#       homepage — the classifier's bare-website
#       fallback said open_website, but the words after
#       the site name are clearly a SEARCH. Pro detects
#       this and converts to youtube_search /
#       google_search with the query extracted.
#     • Search queries missing a fallback — "play lofi
#       on youtube" matched neither of the extractor's
#       search patterns ("play" isn't a search verb
#       there). Pro adds a scaffolding-stripping
#       fallback so the query is recovered.
#     • Whitespace-only text ran the full pipeline —
#       "   " is truthy, so it hit the classifier and
#       semantic parser. Pro treats it as empty.
#     • find_coordinates was never wired — "move the
#       mouse to 100, 200" went unknown → semantic
#       parser. Pro catches it locally and fills x/y.
#
#   ADDITIONS
#     • Result shaping — search → text=query,
#       volume/brightness → text=percent,
#       reminder → text=message, mouse → x/y,
#       so plans build directly from the result
#     • Semantic-fallback enrichment for searches
#     • Bounded analyze() cache for repeated input
#     • get_stats() — local hits, fallbacks, cache
#
# ============================================================
# ============================================================

import re


class NLPEnginePro(NLPEngine):

    # ==================================================
    # INTENTS THAT REQUIRE AN ENTITY TO EXECUTE
    # (extends the base's three open_* intents)
    # ==================================================

    ENTITY_REQUIRED = {
        "open_application",
        "open_website",
        "open_folder",
        "close_application",
        "youtube_search",
        "google_search",
        "set_volume",
        "set_brightness",
        "set_reminder",
        "mouse_move",
    }

    # ==================================================
    # CACHE + STATS
    # ==================================================

    _CACHE = {}

    _CACHE_LIMIT = 256

    _STATS = {
        "requests": 0,
        "local_hits": 0,
        "semantic_fallbacks": 0,
        "missing_entity_fallbacks": 0,
        "search_conversions": 0,
        "mouse_catches": 0,
        "cache_hits": 0,
    }

    # ==================================================
    # HELPERS
    # ==================================================

    @staticmethod
    def _normalize(text):

        return " ".join(
            str(text or "").lower().split()
        )

    # ==================================================
    # ENTITY EXTRACTION FOR EVERY INTENT
    # (the base only knew five)
    # ==================================================

    @classmethod
    def _extract_entity(
        cls,
        intent,
        text,
    ):

        if intent in (
            "open_application",
            "close_application",
        ):

            return (
                EntityExtractor.find_application(
                    text
                )
            )

        if intent == "open_website":

            return (
                EntityExtractor.find_website(
                    text
                )
            )

        if intent == "open_folder":

            return (
                EntityExtractor.find_folder(
                    text
                )
            )

        if intent == "type_text":

            return (
                EntityExtractor.find_typed_text(
                    text
                )
            )

        if intent == "press_key":

            return (
                EntityExtractor.find_key(
                    text
                )
            )

        if intent in (
            "youtube_search",
            "google_search",
        ):

            finder = getattr(
                EntityExtractor,
                "find_search_query",
                None,
            )

            if finder is not None:

                found = finder(text)

                if found:

                    return found

            return cls._search_fallback(
                text
            )

        if intent in (
            "set_volume",
            "set_brightness",
        ):

            finder = getattr(
                EntityExtractor,
                "find_setting",
                None,
            )

            if finder is not None:

                return finder(text)

            return None

        if intent == "set_reminder":

            finder = getattr(
                EntityExtractor,
                "find_reminder",
                None,
            )

            if finder is not None:

                return finder(text)

            return None

        if intent == "mouse_move":

            return (
                EntityExtractor.find_coordinates(
                    text
                )
            )

        return None

    # ==================================================
    # SEARCH FALLBACK
    # Strips command scaffolding around a known
    # engine mention: "play lofi on youtube" → lofi
    # ==================================================

    @staticmethod
    def _search_fallback(text):

        t = NLPEnginePro._normalize(
            text
        )

        engine = None

        if re.search(
            r"\byoutube\b|\byt\b",
            t,
        ):

            engine = "youtube"

        elif re.search(
            r"\bgoogle\b",
            t,
        ):

            engine = "google"

        if engine is None:

            return None

        query = t

        query = re.sub(
            r"^(?:please\s+)?(?:can you\s+)?"
            r"(?:play|search|find|open|launch|"
            r"go to|show me)\s+"
            r"(?:the\s+|a\s+|some\s+)?"
            r"(?:web\s+|video\s+|videos\s+)?"
            r"(?:for\s+|about\s+)?",
            "",
            query,
        )

        query = re.sub(
            r"\s+(?:on|in|at|from|via)\s+"
            r"(?:the\s+)?"
            r"(?:youtube|yt|google)\b",
            "",
            query,
        )

        query = re.sub(
            r"\b(?:youtube|yt|google)\b",
            "",
            query,
        )

        query = re.sub(
            r"^(?:and|then|for|about)\s+",
            "",
            query,
        )

        query = re.sub(
            r"^(?:search|find)"
            r"(?:\s+for|\s+about)?\s+",
            "",
            query,
        )

        query = query.strip(" ,.!?")

        if not query:

            return None

        return {
            "engine": engine,
            "query": query,
        }

    # ==================================================
    # RESULT SHAPING
    # Puts extracted values where the planner and
    # ActionExecutor expect them (additive — the
    # full entity dict is always kept in "entity")
    # ==================================================

    @staticmethod
    def _shape(
        result,
        intent,
        entity,
    ):

        if entity is None:

            return result

        if isinstance(entity, dict):

            if (
                "engine" in entity
                and "query" in entity
            ):

                result["text"] = (
                    entity["query"]
                )

            elif "percent" in entity:

                result["text"] = str(
                    entity["percent"]
                )

            elif intent == "set_reminder":

                result["text"] = (
                    entity.get("message")
                )

            elif (
                "x" in entity
                and "y" in entity
            ):

                result["x"] = entity.get(
                    "x"
                )

                result["y"] = entity.get(
                    "y"
                )

        elif intent == "type_text":

            result["text"] = entity

        elif intent == "press_key":

            result["key"] = entity

        return result

    # ==================================================
    # ANALYZE (extended, same schema)
    # ==================================================

    def analyze(
        self,
        text: str,
    ):

        cleaned = str(
            text or ""
        ).strip()

        # FIX: whitespace-only text no longer
        # runs the whole pipeline.

        if not cleaned:

            return {
                "language": "en",
                "language_name": "English",
                "intent": "unknown",
                "entity": None,
                "text": None,
                "key": None,
                "x": None,
                "y": None,
                "is_command": False,
                "confidence": 0.0,
                "source": "none",
            }

        self._STATS["requests"] += 1

        cache_key = self._normalize(
            cleaned
        )

        cached = self._CACHE.get(
            cache_key
        )

        if cached is not None:

            self._STATS[
                "cache_hits"
            ] += 1

            return dict(cached)

        # ==============================================
        # LANGUAGE (Pro detector via alias)
        # ==============================================

        language = (
            LanguageDetector.detect(
                cleaned
            )
        )

        # ==============================================
        # LOCAL CLASSIFICATION (Pro classifier)
        # ==============================================

        local_intent = (
            IntentClassifier.classify(
                cleaned
            )
        )

        local_entity = None

        # ==============================================
        # FIX: "youtube lofi" / "google weather" —
        # the classifier's bare-website fallback
        # says open_website, but the trailing words
        # are a search. Convert before extraction.
        # ==============================================

        if (
            local_intent == "open_website"
            and hasattr(
                EntityExtractor,
                "find_search_query",
            )
        ):

            search = (
                EntityExtractor
                .find_search_query(
                    cleaned
                )
            )

            if (
                search
                and search.get("engine")
                in ("youtube", "google")
                and search.get("query")
            ):

                local_intent = (
                    search["engine"]
                    + "_search"
                )

                self._STATS[
                    "search_conversions"
                ] += 1

        # ==============================================
        # FIX: local mouse_move catch — the base
        # never wired find_coordinates
        # ==============================================

        if local_intent == "unknown":

            lowered = (
                self._normalize(cleaned)
            )

            if re.search(
                r"\bmove\b|\bmouse\b|\bcursor\b",
                lowered,
            ):

                coords = (
                    EntityExtractor.find_coordinates(
                        cleaned
                    )
                )

                if coords:

                    local_intent = (
                        "mouse_move"
                    )

                    local_entity = coords

                    self._STATS[
                        "mouse_catches"
                    ] += 1

        # ==============================================
        # ENTITY EXTRACTION (all intents)
        # ==============================================

        if local_intent not in (
            "unknown",
            "mouse_move",
        ):

            local_entity = (
                self._extract_entity(
                    local_intent,
                    cleaned,
                )
            )

        # ==============================================
        # FAST RESULT — with validation
        # (FIX: entity now required for ALL
        #  entity-requiring intents, not just
        #  the three open_* ones)
        # ==============================================

        if (
            local_intent != "unknown"
            and (
                local_intent
                not in self.ENTITY_REQUIRED
                or local_entity is not None
            )
        ):

            result = {
                "language": language,
                "language_name":
                    LanguageDetector.name(
                        language
                    ),
                "intent": local_intent,
                "entity": local_entity,
                "text": None,
                "key": None,
                "x": None,
                "y": None,
                "is_command": True,
                "confidence": 0.99,
                "source": "local",
            }

            result = self._shape(
                result,
                local_intent,
                local_entity,
            )

            self._STATS[
                "local_hits"
            ] += 1

            if (
                len(self._CACHE)
                >= self._CACHE_LIMIT
            ):

                self._CACHE.clear()

            self._CACHE[cache_key] = dict(
                result
            )

            return result

        if local_intent in (
            self.ENTITY_REQUIRED
        ):

            self._STATS[
                "missing_entity_fallbacks"
            ] += 1

        # ==============================================
        # MULTILINGUAL SEMANTIC PARSER
        # (same messages as the base)
        # ==============================================

        print()

        print(
            "[NLP] Local rules did not fully understand "
            "the command."
        )

        print(
            "[NLP] Using multilingual semantic parser..."
        )

        semantic = (
            self.semantic_parser.parse(
                cleaned
            )
        )

        intent = semantic.get(
            "intent",
            "unknown"
        )

        target = semantic.get(
            "target"
        )

        typed_text = semantic.get(
            "text"
        )

        key = semantic.get(
            "key"
        )

        x = semantic.get(
            "x"
        )

        y = semantic.get(
            "y"
        )

        confidence = float(
            semantic.get(
                "confidence",
                0.0
            )
        )

        # ==============================================
        # FIX: enrich semantic search results —
        # if the parser found a search intent but
        # no query, recover it locally
        # ==============================================

        if (
            intent in (
                "youtube_search",
                "google_search",
            )
            and not typed_text
        ):

            recovered = (
                self._search_fallback(
                    cleaned
                )
            )

            if recovered:

                typed_text = (
                    recovered["query"]
                )

                target = recovered

        is_command = (
            intent != "unknown"
            and confidence >= 0.60
        )

        result = {
            "language": language,
            "language_name":
                LanguageDetector.name(
                    language
                ),
            "intent": intent,
            "entity": target,
            "text": typed_text,
            "key": key,
            "x": x,
            "y": y,
            "is_command": is_command,
            "confidence": confidence,
            "source": "semantic",
        }

        self._STATS[
            "semantic_fallbacks"
        ] += 1

        if (
            len(self._CACHE)
            >= self._CACHE_LIMIT
        ):

            self._CACHE.clear()

        self._CACHE[cache_key] = dict(
            result
        )

        return result

    # ==================================================
    # STATS
    # ==================================================

    @classmethod
    def get_stats(cls):

        return dict(cls._STATS)


# ------------------------------------------------------------
# DROP-IN UPGRADE
# Anything importing NLPEngine now gets the extended
# version (same analyze() API and result schema).
# Delete the next line to keep the original.
# ------------------------------------------------------------

NLPEngine = NLPEnginePro


# ============================================================
# QUICK TEST (uncomment to try)
# ============================================================
#
# if __name__ == "__main__":
#
#     engine = NLPEngine()
#
#     tests = [
#         # Fixed: new intents now carry entities
#         "close chrome",
#         "play lofi on youtube",
#         "set volume to 40",
#         "remind me in 10 minutes to check the oven",
#         # Fixed: search conversion
#         "youtube lofi beats",
#         "google weather",
#         # Fixed: still opens normally
#         "open youtube",
#         "open google chrome",
#         # Fixed: mouse coordinates wired
#         "move the mouse to 100, 200",
#         # Unchanged behavior
#         "take a screenshot",
#         "what's my battery level",
#         "hello there",
#     ]
#
#     for text in tests:
#
#         result = engine.analyze(text)
#
#         print(
#             f"{text!r} → "
#             f"intent={result['intent']} "
#             f"entity={result['entity']} "
#             f"text={result['text']} "
#             f"xy=({result['x']},{result['y']}) "
#             f"source={result['source']}"
#         )
#
#     print(engine.get_stats())