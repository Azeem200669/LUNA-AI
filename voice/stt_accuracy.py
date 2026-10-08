"""
🌙 LUNA STT ACCURACY BOOSTER

Fixes wrong / wrong-language voice transcripts without
modifying speech_to_text.py. Applies to any SpeechToText
instance (original or Pro) by patching _transcribe.

Improvements:
  • Command-vocabulary initial prompt (Whisper expects your commands)
  • beam_size 3 / best_of 3 decoding (was 1 / 1)
  • Language stickiness — short clips reuse the last confident
    language instead of re-guessing (kills cross-language gibberish)
  • One retry with the known language when detection is uncertain
  • Fuzzy command corrector — near-miss phrases become real commands
  • Optional model upgrade (tiny → base) via config
"""

import re

from collections import deque
from difflib import SequenceMatcher, get_close_matches


# ============================================================
# FUZZY COMMAND CORRECTOR
# ============================================================


class LunaCommandCorrector:

    # ------------------------------------------------
    # Common Whisper mishearings → canonical keyword
    # (extend freely with add_keyword)
    # ------------------------------------------------

    KEYWORD_VARIANTS = {
        "youtube": [
            "utube", "ytube", "youtub", "you tube",
            "utub", "yutube", "youtubs", "u tube",
        ],
        "screenshot": [
            "screen shot", "screenshots", "screenhot",
            "screnshot", "screenchot", "screen shots",
        ],
        "battery": [
            "batory", "bettry", "battry", "batery",
            "batteries", "battary",
        ],
        "volume": [
            "volum", "wolume", "voliume", "valium",
        ],
        "brightness": [
            "brithness", "brightnes", "brighness",
        ],
        "chrome": [
            "krome", "crome", "chrom",
        ],
        "google": [
            "gogle", "googel", "gogol",
        ],
        "luna": [
            "loona", "lunor", "lunar", "lunna",
        ],
        "wifi": [
            "wi-fi", "wyfi", "wify", "weifi",
        ],
        "shutdown": [
            "shut down", "shutdwn", "shotdown",
        ],
        "health": [
            "helth", "heath", "halth",
        ],
        "computer": [
            "comuter", "computor", "compiter",
        ],
        "laptop": [
            "laptop", "laptap",
        ],
        "weather": [
            "wether", "whether", "weathr",
        ],
    }

    # ------------------------------------------------
    # Whole-phrase rescue: if the transcript is CLOSE
    # to a known command, replace it entirely.
    # Only applies to short utterances (≤ 6 words)
    # so real sentences are never hijacked.
    # ------------------------------------------------

    DEFAULT_PHRASES = [
        "open youtube",
        "open chrome",
        "open google",
        "take a screenshot",
        "take a screenshot now",
        "battery status",
        "system health",
        "system status",
        "what time is it",
        "what's the date",
        "wi-fi status",
        "scan wifi",
        "volume up",
        "volume down",
        "mute the volume",
        "who is luna",
    ]

    def __init__(
        self,
        phrase_threshold=0.78,
        token_threshold=0.80,
    ):

        self.phrase_threshold = (
            phrase_threshold
        )

        self.token_threshold = (
            token_threshold
        )

        self.phrases = list(
            self.DEFAULT_PHRASES
        )

        self._variant_index = {}

        self._rebuild_index()

    # ------------------------------------------------
    # INDEX
    # ------------------------------------------------

    def _rebuild_index(self):

        self._variant_index = {}

        for target, variants in (
            self.KEYWORD_VARIANTS.items()
        ):

            entries = list(variants)

            entries.append(target)

            for entry in entries:

                self._variant_index[
                    entry.lower()
                ] = target

    def add_keyword(
        self,
        target,
        variants,
    ):

        self.KEYWORD_VARIANTS[
            str(target).lower()
        ] = [
            str(variant).lower()
            for variant in variants
        ]

        self._rebuild_index()

    def add_phrase(self, phrase):

        phrase = (
            " ".join(
                str(phrase)
                .lower()
                .split()
            )
        )

        if phrase:

            self.phrases.append(
                phrase
            )

    # ------------------------------------------------
    # LOOKUP
    # ------------------------------------------------

    def _variant_lookup(self, token):

        token = str(token).lower()

        if not token:

            return None

        if token in self._variant_index:

            return self._variant_index[
                token
            ]

        if len(token) < 4:

            return None

        matches = get_close_matches(
            token,
            self._variant_index.keys(),
            n=1,
            cutoff=self.token_threshold,
        )

        if matches:

            return self._variant_index[
                matches[0]
            ]

        return None

    # ------------------------------------------------
    # CORRECT
    # ------------------------------------------------

    def correct(self, text):

        original = str(text)

        cleaned = " ".join(
            original.lower().split()
        )

        if not cleaned:

            return original

        words = cleaned.split()

        # ------------------------------------------
        # 1) WHOLE-PHRASE RESCUE
        # ------------------------------------------

        if len(words) <= 6:

            for phrase in self.phrases:

                phrase_words = (
                    phrase.split()
                )

                if (
                    abs(
                        len(words)
                        - len(phrase_words)
                    )
                    > 1
                ):

                    continue

                ratio = (
                    SequenceMatcher(
                        None,
                        cleaned,
                        phrase,
                    )
                    .ratio()
                )

                if (
                    ratio
                    >= self.phrase_threshold
                ):

                    return phrase

        # ------------------------------------------
        # 2) TOKEN-LEVEL FIX (bigrams, then singles)
        # ------------------------------------------

        output = []

        changed = False

        index = 0

        while index < len(words):

            if index + 1 < len(words):

                bigram = (
                    words[index]
                    + " "
                    + words[index + 1]
                )

                target = (
                    self._variant_lookup(
                        bigram
                    )
                )

                if target:

                    output.append(
                        target
                    )

                    changed = True

                    index += 2

                    continue

            target = self._variant_lookup(
                words[index]
            )

            if target:

                output.append(target)

                changed = True

            else:

                output.append(
                    words[index]
                )

            index += 1

        if not changed:

            return original

        corrected = " ".join(output)

        print(
            f"🔧 Corrected transcript: "
            f"'{cleaned}' → '{corrected}'"
        )

        return corrected


# ============================================================
# ACCURACY BOOSTER
# ============================================================


class STTAccuracyBooster:

    # ------------------------------------------------
    # Feeding LUNA's command vocabulary as the
    # initial prompt is the single biggest
    # accuracy win — Whisper now EXPECTS
    # these words.
    # ------------------------------------------------

    INITIAL_PROMPT = (
        "Luna voice commands: open YouTube, "
        "open Chrome, open Google, take a "
        "screenshot, battery status, system "
        "health, volume up, volume down, "
        "Wi-Fi status, what time is it, "
        "set brightness, shutdown, restart, "
        "stop, stop Luna, cancel."
    )

    def __init__(
        self,
        stt,
        corrector=None,
        min_auto_confidence=0.45,
        reject_uncertain=False,
        sticky_language=True,
        sticky_max_seconds=3.0,
    ):

        self.stt = stt

        self.corrector = (
            corrector
            or LunaCommandCorrector()
        )

        # Below this language probability,
        # detection is treated as a guess.

        self.min_auto_confidence = (
            min_auto_confidence
        )

        # If True: uncertain + uncorrectable
        # transcripts return None instead of
        # garbage (LUNA says "didn't catch").

        self.reject_uncertain = (
            reject_uncertain
        )

        self.sticky_language = (
            sticky_language
        )

        self.sticky_max_seconds = (
            sticky_max_seconds
        )

        self.language_history = deque(
            maxlen=3
        )

        self.boosted_count = 0

        self.corrected_count = 0

        self.retried_count = 0

    # ------------------------------------------------
    # INSTALL
    # ------------------------------------------------

    def install(self, model_size=None):

        if model_size:

            self._load_model(
                model_size
            )

        if not hasattr(
            self.stt,
            "_luna_pre_boost_transcribe",
        ):

            self.stt._luna_pre_boost_transcribe = (
                self.stt._transcribe
            )

        self.stt._transcribe = (
            self._boosted_transcribe
        )

        self.stt.corrector = (
            self.corrector
        )

        print(
            "⚡ STT accuracy boost installed."
        )

        return self

    def _load_model(self, model_size):

        try:

            from faster_whisper import (
                WhisperModel,
            )

        except ImportError:

            print(
                "❌ Cannot upgrade model — "
                "faster_whisper missing."
            )

            return

        print(
            f"⚡ Upgrading STT model "
            f"to '{model_size}'..."
        )

        self.stt.model = WhisperModel(
            model_size,
            device="cpu",
            compute_type="int8",
        )

        print(
            f"✅ STT model '{model_size}' ready."
        )

    # ------------------------------------------------
    # LANGUAGE STICKINESS
    # ------------------------------------------------

    def _history_language(self):

        history = list(
            self.language_history
        )

        if len(history) < 2:

            return None

        if len(set(history)) == 1:

            return history[0]

        return None

    def _remember_language(
        self,
        language,
        probability,
    ):

        if (
            language
            and language != "unknown"
            and probability >= 0.70
        ):

            self.language_history.append(
                language
            )

    # ------------------------------------------------
    # BOOSTED TRANSCRIBE
    # ------------------------------------------------

    def _run_model(
        self,
        audio,
        language,
    ):

        kwargs = {
            "language": language,
            "beam_size": 3,
            "best_of": 3,
            "temperature": 0,
            "vad_filter": True,
            "vad_parameters": {
                "min_silence_duration_ms": 450,
            },
            "condition_on_previous_text": False,
            "initial_prompt": (
                self.INITIAL_PROMPT
            ),
        }

        try:

            return self.stt.model.transcribe(
                audio,
                **kwargs,
            )

        except TypeError:

            # Safety for older faster-whisper
            # builds without initial_prompt.

            kwargs.pop(
                "initial_prompt",
                None,
            )

            return self.stt.model.transcribe(
                audio,
                **kwargs,
            )

    @staticmethod
    def _collect(segments):

        parts = []

        for segment in segments:

            text = str(
                getattr(
                    segment,
                    "text",
                    "",
                )
                or ""
            ).strip()

            if text:

                parts.append(text)

        return " ".join(parts).strip()

    def _boosted_transcribe(self, audio):

        self.boosted_count += 1

        sample_rate = (
            getattr(
                self.stt,
                "sample_rate",
                16000,
            )
            or 16000
        )

        duration = (
            len(audio)
            / float(sample_rate)
        )

        # ------------------------------------------
        # PASS 1 — sticky language for short clips
        # ------------------------------------------

        language = None

        if (
            self.sticky_language
            and duration
            <= self.sticky_max_seconds
        ):

            language = (
                self._history_language()
            )

            if language:

                print(
                    f"🎯 Sticky language: "
                    f"{language}"
                )

        segments, info = self._run_model(
            audio,
            language,
        )

        text = self._collect(segments)

        detected = str(
            getattr(info, "language", None)
            or "unknown"
        )

        probability = float(
            getattr(
                info,
                "language_probability",
                0.0,
            )
            or 0.0
        )

        # ------------------------------------------
        # PASS 2 — uncertain auto-detect retry
        # ------------------------------------------

        if (
            language is None
            and probability
            < self.min_auto_confidence
        ):

            candidate = (
                self._history_language()
            )

            if (
                candidate
                and candidate != detected
            ):

                self.retried_count += 1

                print(
                    f"🔁 Uncertain language "
                    f"({detected} "
                    f"{probability:.2f}) — "
                    f"retrying as {candidate}"
                )

                (
                    segments,
                    info,
                ) = self._run_model(
                    audio,
                    candidate,
                )

                retry_text = (
                    self._collect(segments)
                )

                retry_probability = float(
                    getattr(
                        info,
                        "language_probability",
                        0.0,
                    )
                    or 0.0
                )

                if retry_text:

                    text = retry_text

                    detected = str(
                        getattr(
                            info,
                            "language",
                            None,
                        )
                        or candidate
                    )

                    probability = (
                        retry_probability
                    )

        # ------------------------------------------
        # MIRROR BASE BEHAVIOUR
        # (VoiceWorker reads these attributes)
        # ------------------------------------------

        self.stt.last_language = detected

        self.stt.last_language_probability = (
            probability
        )

        self.stt.last_transcription_confidence = (
            probability
        )

        self._remember_language(
            detected,
            probability,
        )

        if not text:

            return None

        # ------------------------------------------
        # HALLUCINATION FILTER (if STT Pro present)
        # ------------------------------------------

        if hasattr(
            self.stt,
            "_clean_text",
        ):

            try:

                cleaned = (
                    self.stt._clean_text(
                        text
                    )
                )

                if not cleaned:

                    return None

                text = cleaned

            except Exception:

                pass

        # ------------------------------------------
        # FUZZY COMMAND CORRECTION
        # ------------------------------------------

        corrected = self.corrector.correct(
            text
        )

        if corrected != text:

            self.corrected_count += 1

        text = corrected

        # ------------------------------------------
        # CONFIDENCE GATE (optional)
        # ------------------------------------------

        if (
            self.reject_uncertain
            and language is None
            and probability
            < self.min_auto_confidence
        ):

            print(
                "🚫 Transcript too uncertain "
                "— asking user to repeat."
            )

            return None

        return text or None

    # ------------------------------------------------
    # STATS
    # ------------------------------------------------

    def get_stats(self):

        return {
            "boosted_transcriptions": (
                self.boosted_count
            ),
            "corrected_transcripts": (
                self.corrected_count
            ),
            "language_retries": (
                self.retried_count
            ),
            "language_history": list(
                self.language_history
            ),
            "vocabulary_phrases": len(
                self.corrector.phrases
            ),
        }


# ============================================================
# ONE-CALL APPLY
# ============================================================


def apply_accuracy_boost(
    stt,
    model_size=None,
    **options,
):

    if model_size is None:

        try:

            import config

            model_size = getattr(
                config,
                "LUNA_STT_MODEL",
                None,
            )

        except Exception:

            model_size = None

    booster = STTAccuracyBooster(
        stt,
        **options,
    )

    booster.install(
        model_size=model_size
    )

    return booster