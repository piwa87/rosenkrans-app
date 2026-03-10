"""Rosary state machine tracking prayer progress through one or more decades."""

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


class RosaryStateMachine:
    """
    State machine for tracking progress through the Catholic Rosary.

    Sequence per decade:
        Our Father  →  10× Hail Mary  →  Glory Be
    Supports up to 5 decades (full Rosary).
    """

    MAX_HAIL_MARYS = 10
    MAX_DECADES = 5

    def __init__(self) -> None:
        self._state = RosaryState()

    def advance(self, prayer: PrayerType) -> RosaryState:
        """Advance the state machine based on the detected prayer type."""
        if prayer == PrayerType.UNKNOWN:
            return self._state

        s = self._state

        if prayer == PrayerType.OUR_FATHER:
            # Start a new decade from IDLE, after Glory Be, or on restart
            if s.state in (DecadeState.IDLE, DecadeState.GLORY_BE, DecadeState.COMPLETE):
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
                if s.decade >= self.MAX_DECADES:
                    s.state = DecadeState.COMPLETE

        s.last_prayer = prayer
        return self._state

    def reset(self) -> None:
        """Reset the state machine to the initial state."""
        self._state = RosaryState()

    def get_state(self) -> RosaryState:
        """Return the current state (read-only reference)."""
        return self._state
