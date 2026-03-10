"""
Rosary Progress Tracker — main entry point.

Audio capture → Whisper STT → prayer detection → state-machine update.

Usage
-----
Console mode (no UI):
    python app/main.py

With web UI (open http://127.0.0.1:5000 in a browser):
    python app/main.py --ui
"""

import logging
import sys
import threading

import numpy as np

from detector import PrayerDetector
from localization import LanguageSettings
from rosary_state import RosaryState, RosaryStateMachine
from stt_whisper import WhisperSTT

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Audio settings
# ---------------------------------------------------------------------------
SAMPLE_RATE = 16_000          # Hz – Whisper expects 16 kHz
# 5-second chunks balance response latency with transcription quality.
# Shorter chunks (<3 s) risk cutting off mid-prayer; longer chunks (>10 s)
# delay detection but give Whisper more context for better accuracy.
CHUNK_SECONDS = 5
CHUNK_SAMPLES = SAMPLE_RATE * CHUNK_SECONDS

# ---------------------------------------------------------------------------
# Shared state machine (also used by the web UI)
# ---------------------------------------------------------------------------
state_machine = RosaryStateMachine()


# ---------------------------------------------------------------------------
# Audio capture backends
# ---------------------------------------------------------------------------

def _capture_pyaudio(chunk_samples: int, sample_rate: int):
    """Yield audio chunks via PyAudio (blocking)."""
    try:
        import pyaudio  # type: ignore[import]
    except ImportError as exc:
        raise ImportError(
            "PyAudio not installed. Run: pip install pyaudio"
        ) from exc

    pa = pyaudio.PyAudio()
    stream = pa.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=sample_rate,
        input=True,
        frames_per_buffer=1024,
    )
    logger.info("Microphone opened (PyAudio, %d Hz).", sample_rate)
    try:
        while True:
            frames = []
            remaining = chunk_samples
            while remaining > 0:
                n = min(1024, remaining)
                data = stream.read(n, exception_on_overflow=False)
                frames.append(data)
                remaining -= n
            raw = b"".join(frames)
            yield np.frombuffer(raw, dtype=np.int16).astype(np.float32)
    finally:
        stream.stop_stream()
        stream.close()
        pa.terminate()


def _capture_sounddevice(chunk_samples: int, sample_rate: int):
    """Yield audio chunks via sounddevice (blocking)."""
    try:
        import sounddevice as sd  # type: ignore[import]
    except ImportError as exc:
        raise ImportError(
            "sounddevice not installed. Run: pip install sounddevice"
        ) from exc

    logger.info("Microphone opened (sounddevice, %d Hz).", sample_rate)
    while True:
        chunk = sd.rec(
            chunk_samples,
            samplerate=sample_rate,
            channels=1,
            dtype="int16",
            blocking=True,
        )
        yield chunk.flatten().astype(np.float32)


def get_audio_stream(chunk_samples: int, sample_rate: int):
    """
    Return an audio-chunk generator using the best available backend.
    Prefers PyAudio, falls back to sounddevice.
    """
    try:
        import pyaudio  # noqa: F401  type: ignore[import]
        return _capture_pyaudio(chunk_samples, sample_rate)
    except ImportError:
        pass
    return _capture_sounddevice(chunk_samples, sample_rate)


# ---------------------------------------------------------------------------
# Processing loop
# ---------------------------------------------------------------------------

def process_loop(
    stt: WhisperSTT,
    detector: PrayerDetector,
    sm: RosaryStateMachine,
    on_state_update=None,
    language_getter=None,
) -> None:
    """
    Main loop: continuously capture audio, transcribe, detect the prayer,
    and advance the state machine.

    Parameters
    ----------
    on_state_update:
        Optional callable invoked with the updated :class:`RosaryState` after
        each successful detection.  Used to push updates to the web UI.
    """
    logger.info(
        "Listening on microphone. Speak prayers aloud — no buttons needed."
    )
    logger.info("Press Ctrl-C to stop.")

    for audio_chunk in get_audio_stream(CHUNK_SAMPLES, SAMPLE_RATE):
        if language_getter is not None:
            stt.language = language_getter()
        transcript = stt.transcribe(audio_chunk, SAMPLE_RATE)
        if not transcript:
            continue

        logger.info("Transcript: %r", transcript)

        prayer = detector.detect(transcript, language=stt.language)
        if prayer is None:
            continue

        state: RosaryState = sm.advance(prayer)

        logger.info(
            "Prayer: %-12s | Decade: %d | Bead: %2d | State: %s",
            prayer.value,
            state.decade,
            state.bead,
            state.state.value,
        )

        if on_state_update is not None:
            on_state_update(state)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    use_ui = "--ui" in sys.argv
    language_settings = LanguageSettings()

    logger.info("=== Rosary Progress Tracker ===")

    stt = WhisperSTT(model_name="base", language=language_settings.get_language())
    detector = PrayerDetector()

    if use_ui:
        from ui.server import create_app, start_ui  # type: ignore[import]

        app = create_app(state_machine, language_settings)

        ui_thread = threading.Thread(
            target=start_ui, args=(app,), daemon=True, name="flask-ui"
        )
        ui_thread.start()
        logger.info("Web UI available at http://127.0.0.1:5000")

    try:
        process_loop(
            stt,
            detector,
            state_machine,
            language_getter=language_settings.get_language,
        )
    except KeyboardInterrupt:
        logger.info("Stopped by user.")


if __name__ == "__main__":
    main()
