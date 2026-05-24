"""
Rosary Progress Tracker — main entry point.

Audio capture → VAD segmentation → Whisper STT → prayer detection → state update.

Architecture
------------
Two threads run concurrently so the microphone is never blocked by transcription:

    capture thread  — reads 30 ms frames from the mic, feeds them to the VAD
                      segmenter, and puts complete utterances into audio_queue.

    main thread     — pulls utterances from audio_queue, runs Whisper, detects
                      the prayer, advances the state machine, and broadcasts the
                      result to SSE clients.

Usage
-----
Console mode (no UI):
    python app/main.py

With web UI (open http://127.0.0.1:5000 in a browser):
    python app/main.py --ui
"""

import argparse
import logging
import queue
import threading
import time

import numpy as np

from audio_vad import FRAME_SAMPLES, SAMPLE_RATE, UtteranceSegmenter
from detector import PrayerDetector
from localization import LanguageSettings
from rosary_state import RosaryState, RosaryStateMachine
from stt_whisper import WhisperSTT

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

state_machine = RosaryStateMachine()


# ---------------------------------------------------------------------------
# Audio capture thread
# ---------------------------------------------------------------------------

def _capture_pyaudio(segmenter: UtteranceSegmenter, audio_queue: "queue.Queue[np.ndarray]") -> None:
    """Capture mic frames via PyAudio and push complete utterances to audio_queue."""
    try:
        import pyaudio  # type: ignore[import]
    except ImportError as exc:
        raise ImportError("PyAudio not installed. Run: pip install pyaudio") from exc

    pa = pyaudio.PyAudio()
    stream = pa.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=SAMPLE_RATE,
        input=True,
        frames_per_buffer=FRAME_SAMPLES,
    )
    logger.info("Microphone opened (PyAudio, %d Hz, %d-sample frames).", SAMPLE_RATE, FRAME_SAMPLES)
    try:
        while True:
            data = stream.read(FRAME_SAMPLES, exception_on_overflow=False)
            frame = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
            utterance = segmenter.feed(frame)
            if utterance is not None:
                try:
                    audio_queue.put_nowait(utterance)
                except queue.Full:
                    logger.warning("Audio queue full — dropping utterance (transcription lagging).")
    finally:
        stream.stop_stream()
        stream.close()
        pa.terminate()


def _capture_sounddevice(segmenter: UtteranceSegmenter, audio_queue: "queue.Queue[np.ndarray]") -> None:
    """Capture mic frames via sounddevice callback and push utterances to audio_queue."""
    try:
        import sounddevice as sd  # type: ignore[import]
    except ImportError as exc:
        raise ImportError("sounddevice not installed. Run: pip install sounddevice") from exc

    def _callback(indata, frames, time_info, status):
        if status:
            logger.debug("sounddevice status: %s", status)
        frame = indata[:, 0].copy()
        utterance = segmenter.feed(frame)
        if utterance is not None:
            try:
                audio_queue.put_nowait(utterance)
            except queue.Full:
                logger.warning("Audio queue full — dropping utterance.")

    logger.info("Microphone opened (sounddevice callback, %d Hz, %d-sample frames).",
                SAMPLE_RATE, FRAME_SAMPLES)
    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32",
        blocksize=FRAME_SAMPLES,
        callback=_callback,
    ):
        while True:
            time.sleep(1)


def _capture_thread(audio_queue: "queue.Queue[np.ndarray]") -> None:
    """Entry point for the audio capture daemon thread."""
    segmenter = UtteranceSegmenter()
    try:
        import pyaudio  # noqa: F401  type: ignore[import]
        _capture_pyaudio(segmenter, audio_queue)
    except ImportError:
        _capture_sounddevice(segmenter, audio_queue)


# ---------------------------------------------------------------------------
# Transcription / detection loop (runs in main thread)
# ---------------------------------------------------------------------------

def process_loop(
    stt: WhisperSTT,
    detector: PrayerDetector,
    sm: RosaryStateMachine,
    audio_queue: "queue.Queue[np.ndarray]",
    on_event=None,
    language_getter=None,
) -> None:
    """
    Pull utterances from audio_queue, transcribe with Whisper, detect prayers,
    and advance the state machine.

    Parameters
    ----------
    on_event:
        Optional callable invoked with ``{"state": ..., "transcript": "..."}``
        after every transcription — even when no prayer is detected — so the
        web UI can show what was heard.
    """
    logger.info("Listening. Speak prayers aloud — no buttons needed.")
    logger.info("Press Ctrl-C to stop.")

    while True:
        utterance = audio_queue.get()

        if language_getter is not None:
            stt.language = language_getter()

        transcript = stt.transcribe(utterance, SAMPLE_RATE)
        if not transcript:
            continue

        logger.info("Transcript: %r", transcript)

        prayer = detector.detect(transcript, language=stt.language)

        if prayer is not None:
            state: RosaryState = sm.advance(prayer)
            logger.info(
                "Prayer: %-12s | Decade: %d | Bead: %2d | State: %s",
                prayer.value, state.decade, state.bead, state.state.value,
            )
        else:
            state = sm.get_state()

        if on_event is not None:
            on_event({"state": state.to_dict(), "transcript": transcript})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Rosary Progress Tracker")
    parser.add_argument("--ui", action="store_true", help="Start the web UI")
    parser.add_argument(
        "--web-stt",
        action="store_true",
        help=(
            "Disable local audio capture; the browser handles mic and speech recognition "
            "via the Web Speech API. Requires --ui. "
            "Useful for mobile use: run the server on a PC/server and open the URL on a phone."
        ),
    )
    parser.add_argument(
        "--model",
        default="small",
        choices=["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"],
        help=(
            "Whisper model size (default: small). "
            "Use 'medium' or 'large' for better accuracy, especially for Danish."
        ),
    )
    args = parser.parse_args()

    language_settings = LanguageSettings()

    logger.info("=== Rosary Progress Tracker ===")
    logger.info("Whisper model: %s", args.model)

    stt = WhisperSTT(model_name=args.model, language=language_settings.get_language())
    detector = PrayerDetector()

    on_event = None
    if args.ui:
        from ui.server import create_app, start_ui  # type: ignore[import]

        app = create_app(state_machine, language_settings, detector=detector)
        on_event = app.broadcast_event  # type: ignore[attr-defined]

        ui_thread = threading.Thread(
            target=start_ui, args=(app,), daemon=True, name="flask-ui"
        )
        ui_thread.start()
        logger.info("Web UI available at http://127.0.0.1:5000")

    if args.web_stt:
        if not args.ui:
            logger.error("--web-stt requires --ui")
            return
        logger.info(
            "Web STT mode: Python audio capture disabled. "
            "Open http://127.0.0.1:5000 on your device and tap the microphone button."
        )
        logger.info("Press Ctrl-C to stop.")
        try:
            threading.Event().wait()  # sleep until KeyboardInterrupt
        except KeyboardInterrupt:
            logger.info("Stopped by user.")
        return

    audio_queue: "queue.Queue[np.ndarray]" = queue.Queue(maxsize=10)

    capture_t = threading.Thread(
        target=_capture_thread,
        args=(audio_queue,),
        daemon=True,
        name="audio-capture",
    )
    capture_t.start()
    logger.info("Audio capture thread started.")

    try:
        process_loop(
            stt,
            detector,
            state_machine,
            audio_queue,
            on_event=on_event,
            language_getter=language_settings.get_language,
        )
    except KeyboardInterrupt:
        logger.info("Stopped by user.")


if __name__ == "__main__":
    main()
