import re


class LanguageDetector:

    LANGUAGE_NAMES = {

        "en": "English",
        "hi": "Hindi",
        "te": "Telugu",
        "ta": "Tamil",
        "kn": "Kannada",
        "ml": "Malayalam",
        "bn": "Bengali",
        "mr": "Marathi",
        "gu": "Gujarati",
        "pa": "Punjabi",
        "ur": "Urdu",
        "ar": "Arabic",
        "fr": "French",
        "es": "Spanish",
        "de": "German",
        "it": "Italian",
        "pt": "Portuguese",
        "ja": "Japanese",
        "ko": "Korean",
        "zh": "Chinese",
    }

    @staticmethod
    def detect(text: str) -> str:

        if not text:
            return "en"

        counts = {
            "te": 0,
            "ta": 0,
            "hi": 0,
            "kn": 0,
            "ml": 0,
            "bn": 0,
            "gu": 0,
            "pa": 0,
            "ur": 0,
            "ar": 0,
            "ja": 0,
            "ko": 0,
            "zh": 0,
        }

        for char in text:

            code = ord(char)

            if 0x0C00 <= code <= 0x0C7F:
                counts["te"] += 1

            elif 0x0B80 <= code <= 0x0BFF:
                counts["ta"] += 1

            elif 0x0900 <= code <= 0x097F:
                counts["hi"] += 1

            elif 0x0C80 <= code <= 0x0CFF:
                counts["kn"] += 1

            elif 0x0D00 <= code <= 0x0D7F:
                counts["ml"] += 1

            elif 0x0980 <= code <= 0x09FF:
                counts["bn"] += 1

            elif 0x0A80 <= code <= 0x0AFF:
                counts["gu"] += 1

            elif 0x0A00 <= code <= 0x0A7F:
                counts["pa"] += 1

            elif 0x0600 <= code <= 0x06FF:
                counts["ur"] += 1

            elif 0x0600 <= code <= 0x06FF:
                counts["ar"] += 1

            elif 0x3040 <= code <= 0x30FF:
                counts["ja"] += 1

            elif 0xAC00 <= code <= 0xD7AF:
                counts["ko"] += 1

            elif 0x4E00 <= code <= 0x9FFF:
                counts["zh"] += 1

        strongest = max(
            counts,
            key=counts.get
        )

        if counts[strongest] > 0:
            return strongest

        return "en"

    @staticmethod
    def name(code: str) -> str:

        return LanguageDetector.LANGUAGE_NAMES.get(
            code,
            "English"
        )


# ============================================================
# ============================================================
#
#   🌙 LUNA LANGUAGE DETECTOR PRO — EXTENSIONS (APPEND ONLY)
#
#   The original LanguageDetector above is 100% unchanged.
#   Pro reimplements detect() (the base loop contains an
#   unreachable branch that can't be fixed by delegation)
#   and keeps every return code compatible.
#
#   FIXES
#     • Arabic branch was DEAD CODE — the Urdu check
#       (identical range) always consumed Arabic-block
#       characters, so Arabic was returned as "ur" 100%
#       of the time and spoken with the Urdu voice.
#       Pro disambiguates with Urdu-specific letters
#       (ٹ ڈ ڑ ں ے گ چ پ ژ) — same convention as the
#       TTS and WebRouter fixes.
#     • Marathi was UNREACHABLE — Devanagari text all
#       counted toward "hi" (both scripts share
#       \u0900-\u097F), and "mr" wasn't even in the
#       counts dict despite being in LANGUAGE_NAMES.
#       Pro routes the Devanagari bucket through
#       marker words (आहे/मध्ये/आणि vs है/में/क्या).
#     • Japanese vs Chinese ties — Kanji (\u4E00-\u9FFF)
#       is shared, so kanji-heavy Japanese counted as
#       "zh". Pro: any kana presence decisively
#       selects "ja" (real Japanese always has kana).
#     • Latin-script languages (fr/es/de/it/pt) were
#       advertised in LANGUAGE_NAMES but could NEVER be
#       returned — detect had no Latin logic. Pro adds
#       conservative marker/stopword scoring.
#
#   ADDITIONS
#     • Thai, Sinhala, Odia script detection
#     • detect_detailed() — code, name, confidence,
#       mixed-script flag, full counts
#     • from_speech(stt, text) — one helper that
#       centralizes the Whisper-language-or-script
#       logic duplicated across VoiceWorker /
#       VoiceManagerPro / _response_language
#     • name() extended for new languages
#     • get_language_names() + get_stats()
#
# ============================================================
# ============================================================


class LanguageDetectorPro(LanguageDetector):

    # ==================================================
    # EXTRA LANGUAGES
    # ==================================================

    EXTRA_LANGUAGE_NAMES = {
        "th": "Thai",
        "si": "Sinhala",
        "or": "Odia",
    }

    # ==================================================
    # URDU vs ARABIC
    # ==================================================

    URDU_LETTERS = "ٹڈڑںےگچپژ"

    # ==================================================
    # MARATHI vs HINDI (shared Devanagari block)
    # ==================================================

    MARATHI_MARKERS = [
        "आहे", "आहेत", "मध्ये", "आणि", "नाही",
        "काय", "तुम्ही", "आपण", "कसे", "किती",
        "मला", "तुला", "पण", "असे", "ते",
    ]

    HINDI_MARKERS = [
        "है", "हैं", "क्या", "कैसे", "कितना",
        "में", "और", "नहीं", "आप", "करो",
        "मुझे", "लेकिन", "यह", "वह", "हूँ",
    ]

    # ==================================================
    # LATIN LANGUAGES (conservative scoring)
    # Char markers score 2 each; stopwords 1 each.
    # A language needs score >= MIN_LATIN_SCORE.
    # ==================================================

    LATIN_CHAR_MARKERS = {
        "es": "ñ¿¡",
        "pt": "ãõ",
        "de": "äöüß",
        "it": "ìò",
        "fr": "œùûô",
    }

    LATIN_STOPWORDS = {
        "fr": {
            "le", "la", "les", "des", "une", "est",
            "et", "du", "au", "ce", "qui", "que",
            "pas", "pour", "avec", "sur", "plus",
            "je", "nous", "vous", "elle", "ils",
            "sont", "dans", "cette", "tout", "ça",
            "bonjour", "merci", "oui", "c'est",
        },
        "es": {
            "el", "los", "las", "una", "que", "con",
            "por", "para", "del", "como", "más",
            "pero", "sus", "este", "esta", "eso",
            "muy", "día", "año", "porque",
            "cuando", "también", "qué", "hay",
            "gracias", "hola", "está", "son",
        },
        "de": {
            "der", "die", "das", "und", "ist",
            "nicht", "mit", "auf", "für", "ein",
            "eine", "ich", "sie", "dem", "den",
            "des", "zu", "auch", "sich", "werden",
            "aus", "wird", "haben", "kann", "aber",
            "über", "kein",
        },
        "it": {
            "il", "lo", "gli", "una", "sono",
            "che", "non", "con", "per", "della",
            "questo", "questa", "più", "anche",
            "come", "nella", "dalla", "perché",
            "molto", "ciao", "grazie",
        },
        "pt": {
            "não", "você", "uma", "dos", "das",
            "pelo", "pela", "isso", "então",
            "muito", "porque", "também", "está",
            "são", "com", "para", "mais", "como",
            "quando", "obrigado", "obrigada",
        },
    }

    MIN_LATIN_LETTERS = 8

    MIN_LATIN_SCORE = 3

    # ==================================================
    # STATS
    # ==================================================

    _STATS = {
        "requests": 0,
        "detected": {},
    }

    # ==================================================
    # LOW-LEVEL SCAN
    # Devanagari and Arabic characters go into
    # buckets first, because each bucket maps to
    # TWO possible languages.
    # ==================================================

    @staticmethod
    def _scan(text):

        counts = {
            "te": 0,
            "ta": 0,
            "or": 0,
            "kn": 0,
            "ml": 0,
            "si": 0,
            "bn": 0,
            "gu": 0,
            "pa": 0,
            "th": 0,
            "ja": 0,
            "ko": 0,
            "zh": 0,
        }

        arabic_chars = 0

        devanagari_chars = 0

        latin_letters = 0

        for char in text:

            code = ord(char)

            if 0x0C00 <= code <= 0x0C7F:
                counts["te"] += 1

            elif 0x0B80 <= code <= 0x0BFF:
                counts["ta"] += 1

            elif 0x0B00 <= code <= 0x0B7F:
                counts["or"] += 1

            elif 0x0900 <= code <= 0x097F:
                devanagari_chars += 1

            elif 0x0C80 <= code <= 0x0CFF:
                counts["kn"] += 1

            elif 0x0D00 <= code <= 0x0D7F:
                counts["ml"] += 1

            elif 0x0D80 <= code <= 0x0DFF:
                counts["si"] += 1

            elif 0x0980 <= code <= 0x09FF:
                counts["bn"] += 1

            elif 0x0A80 <= code <= 0x0AFF:
                counts["gu"] += 1

            elif 0x0A00 <= code <= 0x0A7F:
                counts["pa"] += 1

            elif 0x0600 <= code <= 0x06FF:
                arabic_chars += 1

            elif 0x0E00 <= code <= 0x0E7F:
                counts["th"] += 1

            elif 0x3040 <= code <= 0x30FF:
                counts["ja"] += 1

            elif 0xAC00 <= code <= 0xD7AF:
                counts["ko"] += 1

            elif 0x4E00 <= code <= 0x9FFF:
                counts["zh"] += 1

            elif char.isascii() and char.isalpha():
                latin_letters += 1

        return (
            counts,
            arabic_chars,
            devanagari_chars,
            latin_letters,
        )

    # ==================================================
    # BUCKET RESOLUTION
    # ==================================================

    @classmethod
    def _resolve_buckets(
        cls,
        text,
        counts,
        arabic_chars,
        devanagari_chars,
    ):

        # ------------------------------------------
        # Devanagari bucket → "mr" or "hi"
        # (default "hi" preserves base behaviour)
        # ------------------------------------------

        if devanagari_chars > 0:

            marathi_hits = sum(
                1
                for word in cls.MARATHI_MARKERS
                if word in text
            )

            hindi_hits = sum(
                1
                for word in cls.HINDI_MARKERS
                if word in text
            )

            if marathi_hits > hindi_hits:

                counts["mr"] = (
                    devanagari_chars
                )

            else:

                counts["hi"] = (
                    devanagari_chars
                )

        # ------------------------------------------
        # Arabic bucket → "ur" or "ar"
        # (default "ar" — fixes the dead branch)
        # ------------------------------------------

        if arabic_chars > 0:

            if any(
                letter in text
                for letter in cls.URDU_LETTERS
            ):

                counts["ur"] = arabic_chars

            else:

                counts["ar"] = arabic_chars

        return counts

    # ==================================================
    # LATIN DETECTION
    # ==================================================

    @classmethod
    def _detect_latin(
        cls,
        text,
        latin_letters,
    ):

        if (
            latin_letters
            < cls.MIN_LATIN_LETTERS
        ):

            return None

        lowered = (
            text.lower()
        )

        words = set(
            re.findall(
                r"[a-zà-ÿœæ']+",
                lowered,
            )
        )

        scores = {}

        for code, markers in (
            cls.LATIN_CHAR_MARKERS
            .items()
        ):

            score = sum(
                1
                for marker in markers
                if marker in lowered
            ) * 2

            score += len(
                words
                & cls.LATIN_STOPWORDS.get(
                    code,
                    set(),
                )
            )

            scores[code] = score

        best = max(
            scores,
            key=scores.get,
        )

        if (
            scores[best]
            >= cls.MIN_LATIN_SCORE
        ):

            return best

        return None

    # ==================================================
    # DETECT (fixed)
    # ==================================================

    @classmethod
    def detect(
        cls,
        text: str,
    ) -> str:

        if not text:

            return "en"

        cls._STATS[
            "requests"
        ] += 1

        counts, arabic_chars, devanagari_chars, latin_letters = (
            cls._scan(text)
        )

        cls._resolve_buckets(
            text,
            counts,
            arabic_chars,
            devanagari_chars,
        )

        strongest = max(
            counts,
            key=counts.get,
        )

        if counts[strongest] > 0:

            # --------------------------------------
            # Kana is decisive for Japanese —
            # real Japanese always contains kana,
            # so kanji-heavy text with any kana
            # is Japanese, not Chinese.
            # --------------------------------------

            if (
                counts.get("ja", 0) > 0
                and strongest == "zh"
            ):

                strongest = "ja"

            detected = (
                cls._STATS["detected"]
            )

            detected[strongest] = (
                detected.get(strongest, 0)
                + 1
            )

            return strongest

        latin_code = (
            cls._detect_latin(
                text,
                latin_letters,
            )
        )

        if latin_code:

            detected = (
                cls._STATS["detected"]
            )

            detected[latin_code] = (
                detected.get(latin_code, 0)
                + 1
            )

            return latin_code

        return "en"

    # ==================================================
    # DETAILED DETECTION
    # ==================================================

    @classmethod
    def detect_detailed(
        cls,
        text: str,
    ) -> dict:

        if not text:

            return {
                "code": "en",
                "name": cls.name("en"),
                "confidence": 0.0,
                "is_mixed": False,
                "counts": {},
            }

        counts, arabic_chars, devanagari_chars, latin_letters = (
            cls._scan(text)
        )

        cls._resolve_buckets(
            text,
            counts,
            arabic_chars,
            devanagari_chars,
        )

        code = cls.detect(text)

        total = (
            latin_letters
            + sum(counts.values())
        )

        if code == "en":

            confidence = (
                latin_letters / total
                if total
                else 0.0
            )

        else:

            primary = counts.get(
                code,
                0,
            )

            confidence = (
                primary / total
                if total
                else 0.0
            )

        script_languages = sum(
            1
            for value in counts.values()
            if value > 0
        )

        is_mixed = (
            script_languages > 1
            or (
                script_languages > 0
                and latin_letters > 0
            )
        )

        active_counts = {
            key: value
            for key, value in counts.items()
            if value > 0
        }

        return {
            "code": code,
            "name": cls.name(code),
            "confidence": round(
                confidence,
                3,
            ),
            "is_mixed": is_mixed,
            "counts": active_counts,
        }

    # ==================================================
    # SPEECH INTEGRATION
    # ==================================================

    @classmethod
    def from_speech(
        cls,
        stt,
        text: str,
    ) -> str:

        # Whisper's own detection wins when
        # confident; script analysis of the
        # transcript is the fallback. This is
        # the same rule VoiceWorker applies —
        # now available everywhere in one call.

        language = str(
            getattr(
                stt,
                "last_language",
                "unknown",
            )
            or "unknown"
        )

        probability = float(
            getattr(
                stt,
                "last_language_probability",
                0.0,
            )
            or 0.0
        )

        if (
            language != "unknown"
            and probability >= 0.65
        ):

            return language

        return cls.detect(text)

    # ==================================================
    # NAMES + STATS
    # ==================================================

    @classmethod
    def name(
        cls,
        code: str,
    ) -> str:

        names = dict(
            cls.LANGUAGE_NAMES
        )

        names.update(
            cls.EXTRA_LANGUAGE_NAMES
        )

        return names.get(
            code,
            "English",
        )

    @classmethod
    def get_language_names(cls):

        names = dict(
            cls.LANGUAGE_NAMES
        )

        names.update(
            cls.EXTRA_LANGUAGE_NAMES
        )

        return names

    @classmethod
    def get_stats(cls):

        stats = dict(cls._STATS)

        stats["detected"] = dict(
            cls._STATS["detected"]
        )

        return stats


# ------------------------------------------------------------
# DROP-IN UPGRADE
# Anything that imports LanguageDetector from this file now
# gets the extended version automatically (same API).
# Delete the next line to keep using the original.
# ------------------------------------------------------------

LanguageDetector = LanguageDetectorPro


# ============================================================
# QUICK TEST (uncomment to try)
# ============================================================
#
# if __name__ == "__main__":
#
#     tests = [
#         # FIXED behaviours:
#         ("مرحبا كيف حالك",            "ar"),   # was "ur" (dead branch)
#         ("آپ کیسے ہیں",               "ur"),   # urdu letters present
#         ("मी तुमच्या मदतीला आहे",      "mr"),   # was "hi" (unreachable)
#         ("आप कैसे हैं",               "hi"),
#         ("こんにちは世界",              "ja"),   # kana beats kanji count
#         ("今天天气很好",               "zh"),
#         ("bonjour le chat est sur la table", "fr"),  # was impossible
#         ("el niño está en la casa",   "es"),   # was impossible
#         ("das ist nicht mein Auto",   "de"),   # was impossible
#         ("hello how are you today",   "en"),
#         ("నువ్వు ఎలా ఉన్నావు",         "te"),
#     ]
#
#     for text, expected in tests:
#         result = LanguageDetector.detect(text)
#         mark = "✅" if result == expected else "❌"
#         print(f"{mark} '{text}' → {result}")
#
#     # Detailed view:
#     print(LanguageDetector.detect_detailed("hello क्या हाल"))
#
#     # Speech integration:
#     # code = LanguageDetector.from_speech(stt_instance, transcript)