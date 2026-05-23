"""
VAD-based utterance segmenter.

Replaces fixed 5-second audio chunks with complete-utterance detection:
1. Capture small audio frames (30 ms) continuously
2. Classify each frame as speech or silence
3. Buffer speech frames
4. Yield a complete utterance when a sufficient silence gap is detected

Giving Whisper complete prayer text instead of mid-sentence fragments
dramatically improves transcription accuracy.

Uses ``webrtcvad`` when installed (pip install webrtcvad-wheels) for better
accuracy; falls back to RMS-energy thresholding with no extra dependencies.
"""

import logging
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

SAMPLE_RATE = 16_000
FRAME_MS = 30                                    # webrtcvad requires 10, 20, or 30 ms
FRAME_SAMPLES = SAMPLE_RATE * FRAME_MS // 1000  # 480 samples @ 16 kHz


class UtteranceSegmenter:
    """
    Segments a continuous audio stream into discrete utterances.

    Feed successive 30-ms frames via ``feed()``.  When speech is followed by a
    sufficient silence gap, ``feed()`` returns the concatenated utterance array;
    otherwise it returns ``None``.
    """

    def __init__(
        self,
        sample_rate: int = SAMPLE_RATE,
        frame_ms: int = FRAME_MS,
        energy_threshold: float = 0.005,  # RMS threshold, ≈ −46 dBFS
        silence_ms: int = 800,            # trailing silence that closes an utterance
        min_speech_ms: int = 400,         # discard shorter bursts (noise, coughs)
        max_utterance_ms: int = 30_000,   # safety cap — force-flush very long prayers
    ) -> None:
        self._frame_samples = sample_rate * frame_ms // 1000
        self._silence_frames = max(1, silence_ms // frame_ms)
        self._min_speech_frames = max(1, min_speech_ms // frame_ms)
        self._max_frames = max_utterance_ms // frame_ms
        self._energy_threshold = energy_threshold
        self._sample_rate = sample_rate

        self._vad = None
        try:
            import webrtcvad  # type: ignore[import]
            self._vad = webrtcvad.Vad(2)  # aggressiveness 0–3; 2 = balanced
            logger.info("WebRTC VAD loaded (aggressiveness=2).")
        except ImportError:
            logger.info("webrtcvad not installed — using energy-based VAD.")

        self._buffer: list[np.ndarray] = []
        self._speech_count = 0
        self._silence_count = 0
        self._in_speech = False

    @property
    def frame_samples(self) -> int:
        return self._frame_samples

    def feed(self, frame: np.ndarray) -> Optional[np.ndarray]:
        """
        Feed one audio frame (must be ``frame_samples`` long).

        Parameters
        ----------
        frame:
            Float32 or int16 samples.  int16 is normalised to [-1, 1] automatically.

        Returns
        -------
        np.ndarray or None
            A complete utterance when one is detected, otherwise ``None``.
        """
        frame = self._normalise(frame)

        if self._is_speech(frame):
            self._silence_count = 0
            self._in_speech = True
            self._speech_count += 1
            self._buffer.append(frame)
            if len(self._buffer) >= self._max_frames:
                return self._flush()
        elif self._in_speech:
            self._buffer.append(frame)  # include trailing silence for natural endings
            self._silence_count += 1
            if self._silence_count >= self._silence_frames:
                if self._speech_count >= self._min_speech_frames:
                    return self._flush()
                self._reset()

        return None

    # ------------------------------------------------------------------

    def _normalise(self, frame: np.ndarray) -> np.ndarray:
        frame = frame.flatten().astype(np.float32)
        if np.abs(frame).max() > 1.0:
            frame = frame / 32768.0
        return frame

    def _is_speech(self, frame: np.ndarray) -> bool:
        if self._vad is not None:
            pcm = (frame * 32768).clip(-32768, 32767).astype(np.int16)
            try:
                return self._vad.is_speech(pcm.tobytes(), self._sample_rate)
            except Exception:
                pass
        return float(np.sqrt(np.mean(frame ** 2))) > self._energy_threshold

    def _flush(self) -> np.ndarray:
        utterance = np.concatenate(self._buffer)
        logger.debug("Utterance ready: %.1f s", len(utterance) / self._sample_rate)
        self._reset()
        return utterance

    def _reset(self) -> None:
        self._buffer = []
        self._speech_count = 0
        self._silence_count = 0
        self._in_speech = False
