"""Prayer detection from transcript text using anchor phrases and debounce."""

import logging
import time
import unicodedata
from typing import Dict, Optional

from localization import DEFAULT_LANGUAGE, normalize_language
from rosary_state import PrayerType

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Anchor phrases for each prayer type
# At least one of these phrases must appear in the transcript for detection.
# ---------------------------------------------------------------------------
def _normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.casefold())
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


_RAW_PRAYER_ANCHORS: Dict[str, Dict[PrayerType, list[str]]] = {
    "en": {
        PrayerType.OUR_FATHER: [
            "our father",
            "who art in heaven",
            "hallowed be thy name",
            "thy kingdom come",
            "thy will be done",
            "give us this day",
            "daily bread",
            "forgive us our trespasses",
            "lead us not into temptation",
            "deliver us from evil",
            "for thine is the kingdom",
        ],
        PrayerType.HAIL_MARY: [
            "hail mary",
            "full of grace",
            "the lord is with thee",
            "blessed art thou among women",
            "blessed is the fruit",
            "holy mary",
            "mother of god",
            "pray for us sinners",
            "now and at the hour",
            "hour of our death",
        ],
        PrayerType.GLORY_BE: [
            "glory be",
            "glory be to the father",
            "and to the son",
            "and to the holy spirit",
            "as it was in the beginning",
            "world without end",
            "forever and ever",
        ],
        PrayerType.FATIMA: [
            "o my jesus",
            "forgive us our sins",
            "save us from the fires",
            "lead all souls to heaven",
        ],
    },
    "da": {
        PrayerType.OUR_FATHER: [
            "fader vor",
            "du som er i himlene",
            "helliget vorde dit navn",
            "komme dit rige",
            "ske din vilje",
            "giv os i dag vort daglige brod",
            "forlad os vor skyld",
            "som ogsa vi forlader vore skyldnere",
            "led os ikke i fristelse",
            "fri os fra det onde",
        ],
        PrayerType.HAIL_MARY: [
            "hil dig maria",
            "fuld af nade",
            "herren er med dig",
            "velsignet er du blandt kvinder",
            "velsignet er dit livs frugt",
            "hellige maria",
            "guds moder",
            "bed for os syndere",
            "nu og i vor dodstime",
        ],
        PrayerType.GLORY_BE: [
            "aere vaere faderen",
            "og sonnen",
            "og helliganden",
            "som det var i begyndelsen",
            "er nu og altid",
            "og i al evighed",
        ],
        PrayerType.FATIMA: [
            "o min jesus",
            "tilgiv os vore synder",
            "frels os fra helvedes ild",
            "for alle sjaele til himlen",
        ],
    },
}

PRAYER_ANCHORS: Dict[str, Dict[PrayerType, list[str]]] = {
    language: {
        prayer_type: [_normalize_text(anchor) for anchor in anchors]
        for prayer_type, anchors in prayer_anchors.items()
    }
    for language, prayer_anchors in _RAW_PRAYER_ANCHORS.items()
}

# Default minimum anchor matches needed for a positive detection
DETECTION_THRESHOLD = 1

# Default cooldown (seconds) before the same prayer can be detected again.
# Set to ~15 s so a single prayer prayed over several audio chunks counts once.
DETECTION_COOLDOWN = 15.0


class PrayerDetector:
    """
    Detects which Catholic prayer is being spoken from a text transcript.

    Detection is based on anchor-phrase matching with:
    * A configurable score threshold (minimum matching anchors required).
    * A per-prayer cooldown to prevent double-counting from adjacent audio
      chunks that contain the same prayer.
    """

    def __init__(
        self,
        threshold: int = DETECTION_THRESHOLD,
        cooldown: float = DETECTION_COOLDOWN,
    ) -> None:
        self.threshold = threshold
        self.cooldown = cooldown
        self._last_detection: Dict[PrayerType, float] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def detect(
        self,
        transcript: str,
        language: str = DEFAULT_LANGUAGE,
    ) -> Optional[PrayerType]:
        """
        Detect a prayer type from *transcript*.

        Returns the best-matching :class:`PrayerType` when the anchor score
        meets the threshold and the per-prayer cooldown has elapsed; otherwise
        returns ``None``.
        """
        if not transcript:
            return None

        text = _normalize_text(transcript)
        scores = self._score_transcript(text, language)
        if not scores:
            return None

        best_prayer = max(scores, key=lambda p: scores[p])
        best_score = scores[best_prayer]

        if best_score < self.threshold:
            return None

        now = time.monotonic()
        # float('-inf') means "never detected": now - (-inf) = inf > any cooldown
        elapsed = now - self._last_detection.get(best_prayer, float("-inf"))
        if elapsed < self.cooldown:
            logger.debug(
                "Cooldown active for %s (%.1fs remaining)",
                best_prayer.value,
                self.cooldown - elapsed,
            )
            return None

        self._last_detection[best_prayer] = now
        logger.info(
            "Detected prayer: %s (anchor score=%d)", best_prayer.value, best_score
        )
        return best_prayer

    def reset_cooldowns(self) -> None:
        """Clear all active cooldowns (useful for testing or re-start)."""
        self._last_detection.clear()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _score_transcript(
        self,
        text: str,
        language: str = DEFAULT_LANGUAGE,
    ) -> Dict[PrayerType, int]:
        """Return the number of matching anchor phrases per prayer type."""
        anchors_by_prayer = PRAYER_ANCHORS[normalize_language(language)]
        return {
            prayer_type: sum(1 for anchor in anchors if anchor in text)
            for prayer_type, anchors in anchors_by_prayer.items()
            if any(anchor in text for anchor in anchors)
        }
