"""Rosary state machine tracking prayer progress through one or more decades."""

import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class PrayerType(str, Enum):
    OUR_FATHER = "OUR_FATHER"
    HAIL_MARY = "HAIL_MARY"
    GLORY_BE = "GLORY_BE"
    FATIMA = "FATIMA"
    UNKNOWN = "UNKNOWN"


class DecadeState(str, Enum):
    IDLE = "IDLE"
    OUR_FATHER = "OUR_FATHER"
    HAIL_MARY = "HAIL_MARY"
    GLORY_BE = "GLORY_BE"
    FATIMA = "FATIMA"     # O My Jesus — said after Glory Be of each decade (optional)
    COMPLETE = "COMPLETE"


@dataclass
class RosaryState:
    decade: int = 0
    bead: int = 0
    state: DecadeState = DecadeState.IDLE
    completed_decades: List[int] = field(default_factory=list)
    last_prayer: Optional[PrayerType] = None

    def to_dict(self) -> dict:
        return {
            "decade": self.decade,
            "bead": self.bead,
            "state": self.state.value,
            "completed_decades": list(self.completed_decades),
            "last_prayer": self.last_prayer.value if self.last_prayer else None,
        }

    def clone(self) -> "RosaryState":
        return RosaryState(
            decade=self.decade,
            bead=self.bead,
            state=self.state,
            completed_decades=list(self.completed_decades),
            last_prayer=self.last_prayer,
        )


class RosaryStateMachine:
    """
    Thread-safe state machine for tracking progress through the Catholic Rosary.

    Sequence per decade:
        Our Father  →  10× Hail Mary  →  Glory Be  →  [O My Jesus (optional)]

    The Fatima prayer is an optional step for decades 1–4; at decade 5, Glory Be
    transitions directly to COMPLETE.  Our Father is always accepted from
    GLORY_BE or FATIMA, so the Fatima prayer can be skipped in detection.

    Supports undo (up to MAX_HISTORY steps) and manual one-step advance for use
    as a fallback when speech recognition misses a prayer.
    """

    MAX_HAIL_MARYS = 10
    MAX_DECADES = 5
    MAX_HISTORY = 30

    def __init__(self) -> None:
        self._state = RosaryState()
        self._history: List[RosaryState] = []
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def advance(self, prayer: PrayerType) -> RosaryState:
        """Advance the state machine based on the detected prayer type."""
        with self._lock:
            if prayer == PrayerType.UNKNOWN:
                return self._state
            self._push_history()
            self._apply(prayer)
            return self._state

    def advance_manual(self) -> RosaryState:
        """
        Advance by one step, inferring the next expected prayer from current state.
        Used by the "Next Bead" button as a fallback when recognition misses a prayer.
        """
        with self._lock:
            next_prayer = self._next_expected()
            if next_prayer is None:
                return self._state
            self._push_history()
            self._apply(next_prayer)
            return self._state

    def undo(self) -> Optional[RosaryState]:
        """Revert the last state change. Returns the restored state, or None if empty."""
        with self._lock:
            if not self._history:
                return None
            self._state = self._history.pop()
            return self._state

    def reset(self) -> None:
        """Reset to the initial state and clear history."""
        with self._lock:
            self._state = RosaryState()
            self._history.clear()

    def get_state(self) -> RosaryState:
        """Return the current state (caller must not mutate the returned object)."""
        return self._state

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _push_history(self) -> None:
        self._history.append(self._state.clone())
        if len(self._history) > self.MAX_HISTORY:
            self._history.pop(0)

    def _next_expected(self) -> Optional[PrayerType]:
        """Infer what prayer should come next given the current state."""
        s = self._state
        if s.state == DecadeState.IDLE:
            return PrayerType.OUR_FATHER
        if s.state == DecadeState.OUR_FATHER:
            return PrayerType.HAIL_MARY
        if s.state == DecadeState.HAIL_MARY:
            return PrayerType.HAIL_MARY if s.bead < self.MAX_HAIL_MARYS else PrayerType.GLORY_BE
        if s.state == DecadeState.GLORY_BE:
            return PrayerType.FATIMA
        if s.state == DecadeState.FATIMA:
            return PrayerType.OUR_FATHER
        return None  # COMPLETE — use reset() to start a new Rosary

    def _apply(self, prayer: PrayerType) -> None:
        """Apply one prayer transition. Must be called with _lock held."""
        s = self._state

        if prayer == PrayerType.OUR_FATHER:
            # Accepted from IDLE, after Glory Be (optionally skipping Fatima), or after Fatima.
            # Not accepted from COMPLETE — use reset() to start over.
            if s.state in (DecadeState.IDLE, DecadeState.GLORY_BE, DecadeState.FATIMA):
                s.decade += 1
                s.bead = 0
                s.state = DecadeState.OUR_FATHER

        elif prayer == PrayerType.HAIL_MARY:
            if s.state in (DecadeState.OUR_FATHER, DecadeState.HAIL_MARY):
                if s.bead < self.MAX_HAIL_MARYS:
                    s.bead += 1
                    s.state = DecadeState.HAIL_MARY

        elif prayer == PrayerType.GLORY_BE:
            if s.state == DecadeState.HAIL_MARY:
                s.state = DecadeState.GLORY_BE
                if s.decade not in s.completed_decades:
                    s.completed_decades.append(s.decade)
                # Decade 5: skip the Fatima state and go straight to COMPLETE
                if s.decade >= self.MAX_DECADES:
                    s.state = DecadeState.COMPLETE

        elif prayer == PrayerType.FATIMA:
            # Optional after Glory Be of decades 1–4.
            # At decade 5 Glory Be already transitions to COMPLETE, so GLORY_BE
            # state is never active with decade == 5 when this branch runs.
            if s.state == DecadeState.GLORY_BE:
                s.state = DecadeState.FATIMA

        s.last_prayer = prayer
