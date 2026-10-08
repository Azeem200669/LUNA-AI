import asyncio
import os
import queue
import re
import tempfile
import threading
import time
import edge_tts
import pygame


class TextToSpeech:
    """
    Low-latency multilingual LUNA TTS.

    Main improvements over the previous version:
    1. The full response is NOT synthesized before playback.
    2. Text is split into short speech chunks.
    3. A producer thread synthesizes chunks while the current chunk plays.
    4. Playback starts as soon as the first chunk is ready.
    5. pygame's mixer is initialized only once for the process.
    6. stop() can interrupt generation/playback.
    """

    def __init__(self):
        # ====================================================
        # FAST SPEECH SETTINGS
        # ====================================================

        self.rate = "+8%"
        self.volume = "+0%"
        self.pitch = "+0Hz"

        # Keep chunks short enough to reduce "time to first audio".
        self.max_chunk_chars = 140

        # Generate a couple of chunks ahead while one is playing.
        self.prefetch_chunks = 2

        # ====================================================
        # FEMALE VOICES
        # ====================================================

        self.voice_map = {
            "en": "en-US-JennyNeural",
            "hi": "hi-IN-SwaraNeural",
            "te": "te-IN-ShrutiNeural",
            "ta": "ta-IN-PallaviNeural",
            "kn": "kn-IN-SapnaNeural",
            "ml": "ml-IN-SobhanaNeural",
            "mr": "mr-IN-AarohiNeural",
            "gu": "gu-IN-DhwaniNeural",
            "bn": "bn-IN-TanishaaNeural",
            "pa": "pa-IN-VaaniNeural",
            "ur": "ur-IN-GulNeural",
            "fr": "fr-FR-DeniseNeural",
            "es": "es-ES-ElviraNeural",
            "de": "de-DE-KatjaNeural",
            "it": "it-IT-ElsaNeural",
            "pt": "pt-BR-FranciscaNeural",
            "ja": "ja-JP-NanamiNeural",
            "ko": "ko-KR-SunHiNeural",
            "zh": "zh-CN-XiaoxiaoNeural",
            "ar": "ar-AE-FatimaNeural",
            "tr": "tr-TR-EmelNeural",
            "ru": "ru-RU-SvetlanaNeural",
        }

        self.default_voice = "en-US-JennyNeural"

        self.speaking = False
        self.audio_ready = False

        # Thread-safe stop signal.
        self._stop_event = threading.Event()

        # Prevent two speak() calls on the same instance from racing.
        self._speak_lock = threading.Lock()

        # ====================================================
        # INITIALIZE AUDIO ONCE
        # ====================================================

        try:
            # pygame.mixer is process-global. Do not reinitialize it
            # every time a TTSWorker creates a TextToSpeech instance.
            if pygame.mixer.get_init() is None:
                pygame.mixer.init(
                    frequency=24000,
                    size=-16,
                    channels=2,
                    buffer=256,
                )

            self.audio_ready = True

        except Exception as error:
            print(
                f"❌ Audio initialization error: {error}"
            )
            self.audio_ready = False

    # ========================================================
    # VOICE
    # ========================================================

    def get_voice(self, language="en"):
        if not language:
            language = "en"

        language = (
            str(language)
            .lower()
            .strip()
            .split("-")[0]
        )

        return self.voice_map.get(
            language,
            self.default_voice,
        )

    # ========================================================
    # LANGUAGE FROM TEXT
    # ========================================================

    def detect_text_language(self, text):
        if not text:
            return "en"

        # Telugu
        if re.search(r"[\u0C00-\u0C7F]", text):
            return "te"

        # Tamil
        if re.search(r"[\u0B80-\u0BFF]", text):
            return "ta"

        # Hindi
        if re.search(r"[\u0900-\u097F]", text):
            return "hi"

        # Kannada
        if re.search(r"[\u0C80-\u0CFF]", text):
            return "kn"

        # Malayalam
        if re.search(r"[\u0D00-\u0D7F]", text):
            return "ml"

        # Bengali
        if re.search(r"[\u0980-\u09FF]", text):
            return "bn"

        # Gujarati
        if re.search(r"[\u0A80-\u0AFF]", text):
            return "gu"

        # Gurmukhi
        if re.search(r"[\u0A00-\u0A7F]", text):
            return "pa"

        # Arabic / Urdu
        if re.search(r"[\u0600-\u06FF]", text):
            return "ur"

        # Japanese
        if re.search(r"[\u3040-\u30FF]", text):
            return "ja"

        # Korean
        if re.search(r"[\uAC00-\uD7AF]", text):
            return "ko"

        # Chinese
        if re.search(r"[\u4E00-\u9FFF]", text):
            return "zh"

        return "en"

    # ========================================================
    # CHUNKING
    # ========================================================

    def _split_text(self, text):
        """
        Split response into short, natural speech chunks.

        We first split on sentence boundaries, then break very long
        sentences on commas/spaces. Keeping the first chunk short is
        what reduces time-to-first-audio.
        """
        text = re.sub(r"\s+", " ", str(text).strip())

        if not text:
            return []

        sentences = re.split(
            r"(?<=[.!?。！？])\s+",
            text,
        )

        chunks = []

        for sentence in sentences:
            sentence = sentence.strip()

            if not sentence:
                continue

            if len(sentence) <= self.max_chunk_chars:
                chunks.append(sentence)
                continue

            parts = re.split(
                r"(?<=[,;:，；：])\s+",
                sentence,
            )

            current = ""

            for part in parts:
                part = part.strip()

                if not part:
                    continue

                candidate = (
                    f"{current} {part}".strip()
                    if current
                    else part
                )

                if len(candidate) <= self.max_chunk_chars:
                    current = candidate
                    continue

                if current:
                    chunks.append(current)

                # Hard split long fragments by word boundaries.
                words = part.split()
                current = ""

                for word in words:
                    candidate = (
                        f"{current} {word}".strip()
                        if current
                        else word
                    )

                    if len(candidate) <= self.max_chunk_chars:
                        current = candidate
                    else:
                        if current:
                            chunks.append(current)

                        # Extremely long single token.
                        if len(word) > self.max_chunk_chars:
                            for start in range(
                                0,
                                len(word),
                                self.max_chunk_chars,
                            ):
                                chunks.append(
                                    word[
                                        start:start
                                        + self.max_chunk_chars
                                    ]
                                )
                        else:
                            current = word

            if current:
                chunks.append(current)

        return chunks

    # ========================================================
    # GENERATE ONE CHUNK
    # ========================================================

    async def _generate(
        self,
        text,
        voice,
        output_file,
    ):
        communicate = edge_tts.Communicate(
            text=text,
            voice=voice,
            rate=self.rate,
            volume=self.volume,
            pitch=self.pitch,
        )

        await communicate.save(output_file)

    # ========================================================
    # GENERATE CHUNK PRODUCER
    # ========================================================

    def _generate_chunk(
        self,
        text,
        voice,
    ):
        """
        Synthesize one short chunk.

        Returns a temporary MP3 path or None when stopped/error.
        """
        if self._stop_event.is_set():
            return None

        output_file = None

        try:
            with tempfile.NamedTemporaryFile(
                suffix=".mp3",
                delete=False,
            ) as temp:
                output_file = temp.name

            asyncio.run(
                self._generate(
                    text,
                    voice,
                    output_file,
                )
            )

            if self._stop_event.is_set():
                self._safe_remove(output_file)
                return None

            return output_file

        except Exception as error:
            print(
                f"❌ TTS chunk generation error: {error}"
            )

            self._safe_remove(output_file)

            return None

    # ========================================================
    # BACKGROUND PRODUCER
    # ========================================================

    def _producer(
        self,
        chunks,
        voice,
        output_queue,
    ):
        try:
            for chunk in chunks:
                if self._stop_event.is_set():
                    break

                output_file = self._generate_chunk(
                    chunk,
                    voice,
                )

                if output_file is None:
                    break

                # Put generated audio into the playback queue.
                while not self._stop_event.is_set():
                    try:
                        output_queue.put(
                            output_file,
                            timeout=0.10,
                        )
                        output_file = None
                        break

                    except queue.Full:
                        continue

                # If stopped before the path could be queued.
                if output_file:
                    self._safe_remove(output_file)
                    break

        finally:
            # Sentinel indicates that no more chunks will arrive.
            # Use a retry loop because the queue is intentionally bounded.
            while True:
                try:
                    output_queue.put(None, timeout=0.10)
                    break
                except queue.Full:
                    if self._stop_event.is_set():
                        break

    # ========================================================
    # SPEAK
    # ========================================================

    def speak(
        self,
        text,
        language=None,
    ):
        if not text:
            return False

        if (
            not language
            or language == "unknown"
        ):
            language = self.detect_text_language(text)

        language = (
            str(language)
            .lower()
            .strip()
            .split("-")[0]
        )

        voice = self.get_voice(language)

        print()
        print("🔊 LUNA TTS")
        print(f"Language: {language}")
        print(f"Voice: {voice}")

        if not self.audio_ready:
            print("❌ Audio system unavailable.")
            return False

        chunks = self._split_text(text)

        if not chunks:
            return False

        with self._speak_lock:
            self._stop_event.clear()
            self.speaking = True

            output_queue = queue.Queue(
                maxsize=max(1, self.prefetch_chunks)
            )

            producer = threading.Thread(
                target=self._producer,
                args=(
                    chunks,
                    voice,
                    output_queue,
                ),
                name="LUNA-TTS-Producer",
                daemon=True,
            )

            producer.start()

            success = False
            finished = False

            try:
                while (
                    not self._stop_event.is_set()
                    and not finished
                ):
                    try:
                        output_file = output_queue.get(
                            timeout=0.10
                        )
                    except queue.Empty:
                        continue

                    if output_file is None:
                        finished = True
                        break

                    if self._stop_event.is_set():
                        self._safe_remove(output_file)
                        break

                    try:
                        # Playback begins as soon as the FIRST chunk
                        # has been synthesized.
                        pygame.mixer.music.load(
                            output_file
                        )

                        pygame.mixer.music.play()

                        success = True

                        while (
                            pygame.mixer.music.get_busy()
                            and not self._stop_event.is_set()
                        ):
                            pygame.time.wait(15)

                    except Exception as error:
                        print(
                            f"❌ TTS playback error: {error}"
                        )
                        break

                    finally:
                        self._safe_remove(output_file)

                return success

            except Exception as error:
                print(
                    f"❌ TTS error: {error}"
                )
                return False

            finally:
                self._stop_event.set()

                try:
                    pygame.mixer.music.stop()
                except Exception:
                    pass

                # Don't leave generated audio behind.
                while True:
                    try:
                        pending = output_queue.get_nowait()
                    except queue.Empty:
                        break

                    if pending:
                        self._safe_remove(pending)

                self.speaking = False

                # Producer is daemonized but should normally exit quickly.
                if producer.is_alive():
                    producer.join(timeout=0.5)

    # ========================================================
    # STOP
    # ========================================================

    def stop(self):
        self._stop_event.set()
        self.speaking = False

        try:
            pygame.mixer.music.stop()
        except Exception:
            pass

    # ========================================================
    # CLEANUP
    # ========================================================

    @staticmethod
    def _safe_remove(path):
        if not path:
            return

        try:
            os.remove(path)
        except (FileNotFoundError, PermissionError, OSError):
            pass


# ============================================================
# ============================================================
#
#   🌙 LUNA TEXT-TO-SPEECH PRO — EXTENSIONS (APPEND ONLY)
#
#   The original TextToSpeech above is 100% unchanged.
#   The base producer/playback pipeline is reused as-is —
#   Pro only swaps the chunk generator underneath it.
#
#   FIXES
#     • _split_text duplication bug — after hard-splitting an
#       extremely long token, `current` kept its old value, so
#       the previous fragment was appended AGAIN on the next
#       word (repeated audio). Corrected in Pro's splitter.
#     • Zero-byte MP3s accepted — edge-tts failures sometimes
#       write an empty file that then plays as silence or
#       errors. Pro validates file size and retries.
#     • Arabic text spoken with the Urdu voice — the original
#       detector maps the whole Arabic block to "ur". Pro
#       disambiguates using Urdu-specific letters (ٹ ڈ ڑ ں
#       ے گ چ پ ژ) → "ur", otherwise "ar".
#
#   ADDITIONS
#     • Speech cleaner — markdown, code blocks, URLs and
#       emoji stripped before synthesis (no more reading
#       "asterisk asterisk" aloud)
#     • Automatic retries with backoff per chunk
#     • Disk cache for synthesized audio (repeated phrases
#       like "Goodbye. See you later." are instant + offline)
#     • Offline fallback — if edge-tts is unreachable, chunks
#       are synthesized by Windows built-in voices (SAPI)
#     • Voice/rate/volume/pitch settings API
#     • preview_voice(), speak_to_file(), list_online_voices()
#     • on_speak_start / on_speak_end hooks + get_stats()
#
# ============================================================
# ============================================================

import hashlib
import shutil
import subprocess

from pathlib import Path


class TextToSpeechPro(TextToSpeech):

    # ==================================================
    # SETTINGS
    # ==================================================

    generation_retries = 2

    cache_max_files = 400

    def __init__(self):

        super().__init__()

        # -----------------------------
        # CACHE
        # -----------------------------

        self.cache_enabled = True

        self._cache_dir = (
            Path.home()
            / "AppData"
            / "Local"
            / "LUNA"
            / "TTS_Cache"
        )

        try:

            self._cache_dir.mkdir(
                parents=True,
                exist_ok=True,
            )

        except Exception:

            self.cache_enabled = False

        # -----------------------------
        # OFFLINE STATE
        # (reset at the start of every
        #  speak so network recovery is
        #  picked up automatically)
        # -----------------------------

        self._offline = False

        self._offline_warned = False

        # -----------------------------
        # HOOKS + STATS
        # -----------------------------

        self.on_speak_start = None

        self.on_speak_end = None

        self._stats = {
            "speaks": 0,
            "chunks_generated": 0,
            "cache_hits": 0,
            "retries": 0,
            "offline_fallbacks": 0,
            "chars_spoken": 0,
        }

    # ==================================================
    # FIX: LANGUAGE DETECTION (Arabic vs Urdu)
    # ==================================================

    def detect_text_language(self, text):

        if text and re.search(
            r"[\u0600-\u06FF]",
            text,
        ):

            urdu_letters = "ٹڈڑںےگچپژ"

            if any(
                letter in text
                for letter in urdu_letters
            ):

                return "ur"

            return "ar"

        return super().detect_text_language(
            text
        )

    # ==================================================
    # SPEECH CLEANER
    # ==================================================

    def _clean_for_speech(self, text):

        text = str(text or "")

        # fenced code blocks — never read code aloud

        text = re.sub(
            r"```.*?```",
            " ",
            text,
            flags=re.S,
        )

        # inline code keeps its content

        text = re.sub(
            r"`([^`]*)`",
            r"\1",
            text,
        )

        # links [text](url) → text

        text = re.sub(
            r"\[([^\]]+)\]\([^)]*\)",
            r"\1",
            text,
        )

        # bare URLs — unreadable noise

        text = re.sub(
            r"https?://\S+",
            " ",
            text,
        )

        # markdown emphasis / headers / quotes / tables

        text = re.sub(
            r"[*_#>`~|]",
            " ",
            text,
        )

        # emoji & symbol decorations

        text = re.sub(
            "["
            "\U0001F000-\U0001FAFF"
            "\U00002600-\U000027BF"
            "\U0001F1E6-\U0001F1FF"
            "\u2190-\u21FF"
            "\u2B00-\u2BFF"
            "\uFE0F\u200D"
            "]+",
            " ",
            text,
        )

        return re.sub(
            r"\s+",
            " ",
            text,
        ).strip()

    # ==================================================
    # FIX: SPLITTER (identical algorithm, bug corrected)
    # ==================================================

    def _split_text(self, text):

        cleaned = self._clean_for_speech(
            text
        )

        if not cleaned:

            return []

        return self._split_cleaned(
            cleaned
        )

    def _split_cleaned(self, text):

        sentences = re.split(
            r"(?<=[.!?。！？])\s+",
            text,
        )

        chunks = []

        for sentence in sentences:

            sentence = sentence.strip()

            if not sentence:

                continue

            if (
                len(sentence)
                <= self.max_chunk_chars
            ):

                chunks.append(sentence)

                continue

            parts = re.split(
                r"(?<=[,;:，；：])\s+",
                sentence,
            )

            current = ""

            for part in parts:

                part = part.strip()

                if not part:

                    continue

                candidate = (
                    f"{current} {part}".strip()
                    if current
                    else part
                )

                if (
                    len(candidate)
                    <= self.max_chunk_chars
                ):

                    current = candidate

                    continue

                if current:

                    chunks.append(current)

                words = part.split()

                current = ""

                for word in words:

                    candidate = (
                        f"{current} {word}".strip()
                        if current
                        else word
                    )

                    if (
                        len(candidate)
                        <= self.max_chunk_chars
                    ):

                        current = candidate

                    else:

                        if current:

                            chunks.append(
                                current
                            )

                        if (
                            len(word)
                            > self.max_chunk_chars
                        ):

                            for start in range(
                                0,
                                len(word),
                                self.max_chunk_chars,
                            ):

                                chunks.append(
                                    word[
                                        start:start
                                        + self.max_chunk_chars
                                    ]
                                )

                            # ★ FIX: the original left
                            # `current` holding the stale
                            # fragment here, duplicating it
                            # on the next word.

                            current = ""

                        else:

                            current = word

            if current:

                chunks.append(current)

        return chunks

    # ==================================================
    # CACHE-AWARE DELETE
    # (the base playback loop deletes every temp file
    #  after playing — this keeps cached files alive)
    # ==================================================

    def _safe_remove(self, path):

        if not path:

            return

        if self.cache_enabled:

            try:

                resolved = (
                    Path(path).resolve()
                )

                if str(resolved).startswith(
                    str(
                        self._cache_dir.resolve()
                    )
                ):

                    return

            except Exception:

                pass

        try:

            os.remove(path)

        except (
            FileNotFoundError,
            PermissionError,
            OSError,
        ):

            pass

    # ==================================================
    # CACHE HELPERS
    # ==================================================

    def _cache_key(self, text, voice):

        raw = (
            f"{voice}|{self.rate}|"
            f"{self.volume}|{self.pitch}|{text}"
        )

        return hashlib.sha1(
            raw.encode("utf-8")
        ).hexdigest()

    def _store_cache(self, source, target):

        if not self.cache_enabled:

            return

        try:

            shutil.copyfile(
                source,
                target,
            )

            files = list(
                self._cache_dir.glob("*.mp3")
            )

            if (
                len(files)
                > self.cache_max_files
            ):

                files.sort(
                    key=lambda item: item.stat()
                    .st_mtime
                )

                for old in files[
                    : len(files)
                    - self.cache_max_files
                ]:

                    try:

                        old.unlink()

                    except Exception:

                        pass

        except Exception:

            pass

    # ==================================================
    # OFFLINE FALLBACK (Windows SAPI)
    # ==================================================

    def _sapi_chunk(self, text):

        try:

            with tempfile.NamedTemporaryFile(
                suffix=".wav",
                delete=False,
            ) as wav_temp:

                wav_path = wav_temp.name

            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".txt",
                delete=False,
                encoding="utf-8",
            ) as txt_temp:

                txt_temp.write(text)

                txt_path = txt_temp.name

            no_window = getattr(
                subprocess,
                "CREATE_NO_WINDOW",
                0,
            )

            script = (
                "$ErrorActionPreference='Stop';"
                "Add-Type -AssemblyName "
                "System.Speech;"
                "$s=New-Object "
                "System.Speech.Synthesis."
                "SpeechSynthesizer;"
                "$s.Rate=1;"
                f"$s.SetOutputToWaveFile("
                f"'{wav_path}');"
                "$s.Speak("
                "[System.IO.File]::ReadAllText("
                f"'{txt_path}'));"
                "$s.Dispose();"
            )

            subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    script,
                ],
                capture_output=True,
                timeout=20,
                creationflags=no_window,
            )

            try:

                os.remove(txt_path)

            except Exception:

                pass

            if os.path.getsize(wav_path) > 44:

                return wav_path

            self._safe_remove(wav_path)

        except Exception as error:

            print(
                f"❌ Offline voice error: {error}"
            )

        return None

    # ==================================================
    # CHUNK GENERATION (retry + cache + fallback)
    # The base _producer calls this transparently.
    # ==================================================

    def _generate_chunk(
        self,
        text,
        voice,
    ):

        if self._stop_event.is_set():

            return None

        # -----------------------------
        # CACHE HIT
        # -----------------------------

        if self.cache_enabled:

            cached = (
                self._cache_dir
                / (
                    self._cache_key(
                        text,
                        voice,
                    )
                    + ".mp3"
                )
            )

            if (
                cached.exists()
                and cached.stat().st_size > 100
            ):

                self._stats[
                    "cache_hits"
                ] += 1

                return str(cached)

        # -----------------------------
        # OFFLINE MODE
        # -----------------------------

        if self._offline:

            self._stats[
                "offline_fallbacks"
            ] += 1

            return self._sapi_chunk(text)

        # -----------------------------
        # ONLINE — WITH RETRIES
        # -----------------------------

        last_error = None

        for attempt in range(
            self.generation_retries
        ):

            if self._stop_event.is_set():

                return None

            output_file = None

            try:

                with tempfile.NamedTemporaryFile(
                    suffix=".mp3",
                    delete=False,
                ) as temp:

                    output_file = temp.name

                asyncio.run(
                    self._generate(
                        text,
                        voice,
                        output_file,
                    )
                )

                if self._stop_event.is_set():

                    self._safe_remove(
                        output_file
                    )

                    return None

                # ★ FIX: validate size — edge-tts
                # can write empty files on failure.

                if (
                    os.path.getsize(
                        output_file
                    )
                    > 100
                ):

                    self._stats[
                        "chunks_generated"
                    ] += 1

                    if self.cache_enabled:

                        self._store_cache(
                            output_file,
                            self._cache_dir
                            / (
                                self._cache_key(
                                    text,
                                    voice,
                                )
                                + ".mp3"
                            ),
                        )

                    return output_file

                last_error = (
                    "empty audio received"
                )

                self._safe_remove(output_file)

            except Exception as error:

                last_error = error

                self._safe_remove(
                    output_file
                )

            self._stats["retries"] += 1

            time.sleep(
                0.35 * (attempt + 1)
            )

        # -----------------------------
        # ALL ATTEMPTS FAILED
        # -----------------------------

        self._offline = True

        self._stats[
            "offline_fallbacks"
        ] += 1

        if not self._offline_warned:

            self._offline_warned = True

            print(
                "⚠️ edge-tts unreachable "
                f"({last_error}) — switching to "
                "Windows offline voices."
            )

        return self._sapi_chunk(text)

    # ==================================================
    # SPEAK WRAPPER (hooks + stats + offline reset)
    # ==================================================

    def speak(self, text, language=None):

        self._offline = False

        self._offline_warned = False

        self._stats["speaks"] += 1

        if text:

            self._stats[
                "chars_spoken"
            ] += len(str(text))

        if self.on_speak_start:

            try:

                self.on_speak_start()

            except Exception:

                pass

        try:

            return super().speak(
                text,
                language,
            )

        finally:

            if self.on_speak_end:

                try:

                    self.on_speak_end()

                except Exception:

                    pass

    # ==================================================
    # SETTINGS API
    # ==================================================

    def set_voice(self, language, voice_name):

        self.voice_map[
            str(language).lower().strip()
        ] = str(voice_name)

    def set_rate(self, rate):

        rate = str(rate).strip()

        if re.fullmatch(
            r"[+-]\d+%",
            rate,
        ):

            self.rate = rate

    def set_volume(self, volume):

        volume = str(volume).strip()

        if re.fullmatch(
            r"[+-]\d+%",
            volume,
        ):

            self.volume = volume

    def set_pitch(self, pitch):

        pitch = str(pitch).strip()

        if re.fullmatch(
            r"[+-]\d+Hz",
            pitch,
        ):

            self.pitch = pitch

    # ==================================================
    # PREVIEW / EXPORT / DISCOVERY
    # ==================================================

    def preview_voice(
        self,
        language="en",
        sample=None,
    ):

        sample = sample or (
            "Hello! This is how I sound "
            "in this language."
        )

        return self.speak(
            sample,
            language=language,
        )

    def speak_to_file(
        self,
        text,
        output_path,
        language=None,
    ):

        text = self._clean_for_speech(
            text
        )

        if not text:

            return False

        if (
            not language
            or language == "unknown"
        ):

            language = (
                self.detect_text_language(
                    text
                )
            )

        voice = self.get_voice(language)

        try:

            asyncio.run(
                self._generate(
                    text,
                    voice,
                    str(output_path),
                )
            )

            return (
                os.path.getsize(
                    str(output_path)
                )
                > 100
            )

        except Exception as error:

            print(
                f"❌ speak_to_file error: {error}"
            )

            return False

    def list_online_voices(
        self,
        language_prefix=None,
    ):

        try:

            voices = asyncio.run(
                edge_tts.list_voices()
            )

        except Exception as error:

            print(
                f"❌ Voice list error: {error}"
            )

            return []

        results = []

        for voice in voices:

            name = str(
                voice.get("ShortName", "")
            )

            if language_prefix and not name.lower().startswith(
                str(language_prefix).lower()
            ):

                continue

            results.append(
                {
                    "name": name,
                    "gender": str(
                        voice.get(
                            "Gender",
                            "",
                        )
                    ),
                }
            )

        return results

    # ==================================================
    # STATS
    # ==================================================

    def get_stats(self):

        stats = dict(self._stats)

        stats["offline"] = self._offline

        stats["cache_enabled"] = (
            self.cache_enabled
        )

        if self.cache_enabled:

            try:

                stats["cached_files"] = len(
                    list(
                        self._cache_dir.glob(
                            "*.mp3"
                        )
                    )
                )

            except Exception:

                stats["cached_files"] = None

        return stats


# ------------------------------------------------------------
# DROP-IN UPGRADE
# Both voice_worker.py and the window's TTSWorker import
# TextToSpeech from this file and now get the extended
# version automatically (same API, more resilience).
# Delete the next line to keep using the original.
# ------------------------------------------------------------

TextToSpeech = TextToSpeechPro


# ============================================================
# QUICK TEST (uncomment to try)
# ============================================================
#
# if __name__ == "__main__":
#
#     tts = TextToSpeech()
#
#     # 1. Normal speech (streams chunk-by-chunk as before)
#     tts.speak("Hello! I'm LUNA. **This** markdown is cleaned.")
#
#     # 2. Stats — check cache hits on the second identical call
#     tts.speak("Goodbye. See you later.")
#     tts.speak("Goodbye. See you later.")
#     print(tts.get_stats())
#
#     # 3. Export audio
#     tts.speak_to_file("Hello world", "hello.mp3")