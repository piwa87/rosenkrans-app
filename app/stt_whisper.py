"""Whisper speech-to-text wrapper (runs locally, no cloud dependency)."""

import logging
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Language-specific initial prompts
# ---------------------------------------------------------------------------
# Providing a short prayer-vocabulary prompt lets Whisper calibrate its
# language model to the expected domain (Catholic prayers) and character set
# (including Danish diacritics æ, ø, å).  This significantly improves
# recognition accuracy for non-English languages like Danish.
_INITIAL_PROMPTS: dict[str, str] = {
    "da": (
        "Fadervor, som er i himlene, helliget vorde dit navn, komme dit rige, ske din vilje. "
        "Hil dig Maria, fuld af nåde, Herren er med dig. "
        "Hellige Maria, Guds Moder, bed for os syndere nu og i vor dødstime. Amen. "
        "Ære være Faderen og Sønnen og Helligånden, i al evighed. Amen."
    ),
}


class WhisperSTT:
    """
    Thin wrapper around the openai-whisper local model.

    The model is loaded lazily on first use so startup is fast and the model
    file is only downloaded/cached once.
    """

    def __init__(self, model_name: str = "base", language: str = "en") -> None:
        self.model_name = model_name
        self.language = language
        self._model = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def transcribe(self, audio: np.ndarray, sample_rate: int = 16000) -> str:
        """
        Transcribe a chunk of audio to text.

        Parameters
        ----------
        audio:
            1-D array of audio samples.  int16 or float32 are both accepted.
        sample_rate:
            Sample rate of the supplied audio.  Whisper expects 16 000 Hz; the
            audio is resampled automatically when ``sample_rate`` differs.

        Returns
        -------
        str
            Transcribed text, or an empty string on error.
        """
        model = self._get_model()
        if model is None:
            return ""

        audio_f32 = self._to_float32(audio)

        # Resample to 16 kHz if needed
        if sample_rate != 16000:
            audio_f32 = self._resample(audio_f32, sample_rate, 16000)

        # Skip near-silent chunks to avoid wasting time on noise
        if self._is_silent(audio_f32):
            logger.debug("Audio chunk is silent; skipping transcription.")
            return ""

        try:
            transcribe_kwargs: dict = {
                "language": self.language,
                "fp16": False,
                "verbose": False,
                # Beam search gives more accurate transcripts than greedy
                # decoding, which is especially beneficial for non-English
                # languages such as Danish.
                "beam_size": 5,
                # Deterministic output: try only temperature=0 (no fallback
                # to higher temperatures).  Reduces hallucinations for short
                # prayer chunks.
                "temperature": 0.0,
                # Do not feed previous chunk text as a prompt for the next
                # chunk; avoids error propagation across chunk boundaries.
                "condition_on_previous_text": False,
            }
            initial_prompt = _INITIAL_PROMPTS.get(self.language)
            if initial_prompt:
                transcribe_kwargs["initial_prompt"] = initial_prompt

            result = model.transcribe(audio_f32, **transcribe_kwargs)
            text: str = result.get("text", "").strip()
            logger.debug("Transcript: %r", text)
            return text
        except Exception as exc:
            logger.error("Transcription error: %s", exc)
            return ""

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_model(self):
        """Load and cache the Whisper model."""
        if self._model is None:
            try:
                import whisper  # type: ignore[import]

                logger.info("Loading Whisper model '%s'…", self.model_name)
                self._model = whisper.load_model(self.model_name)
                logger.info("Whisper model loaded.")
            except ImportError as exc:
                raise ImportError(
                    "openai-whisper is not installed. "
                    "Run: pip install openai-whisper"
                ) from exc
        return self._model

    @staticmethod
    def _to_float32(audio: np.ndarray) -> np.ndarray:
        audio = audio.flatten().astype(np.float32)
        if audio.max() > 1.0 or audio.min() < -1.0:
            # Assume int16 range → normalise to [-1, 1]
            audio = audio / 32768.0
        return audio

    @staticmethod
    def _resample(audio: np.ndarray, orig_rate: int, target_rate: int) -> np.ndarray:
        """Naive linear interpolation resample (sufficient for speech)."""
        if orig_rate == target_rate:
            return audio
        ratio = target_rate / orig_rate
        new_length = int(len(audio) * ratio)
        indices = np.linspace(0, len(audio) - 1, new_length)
        return np.interp(indices, np.arange(len(audio)), audio).astype(np.float32)

    @staticmethod
    def _is_silent(audio: np.ndarray, rms_threshold: float = 0.002) -> bool:
        """
        Return True when the audio chunk is below the RMS silence threshold.

        The default threshold of 0.002 (relative to a [-1, 1] float32 range)
        corresponds roughly to -54 dBFS — quiet enough to skip background hiss
        and room noise while still detecting soft speech.  Adjust upward for
        noisy environments or downward for very quiet microphones.
        """
        rms = float(np.sqrt(np.mean(audio**2)))
        return rms < rms_threshold
