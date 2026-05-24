"""Tests for the RosaryStateMachine."""

import pytest

from rosary_state import DecadeState, PrayerType, RosaryStateMachine


@pytest.fixture()
def sm():
    return RosaryStateMachine()


def _full_decade(sm, decade_number=None):
    """Helper: advance through a complete decade (Our Father → 10 HM → Glory Be)."""
    sm.advance(PrayerType.OUR_FATHER)
    for _ in range(10):
        sm.advance(PrayerType.HAIL_MARY)
    sm.advance(PrayerType.GLORY_BE)


# ── Initial state ─────────────────────────────────────────────────────────────

def test_initial_state(sm):
    s = sm.get_state()
    assert s.decade == 0
    assert s.bead == 0
    assert s.state == DecadeState.IDLE
    assert s.completed_decades == []
    assert s.last_prayer is None


# ── Our Father ────────────────────────────────────────────────────────────────

def test_our_father_starts_decade(sm):
    s = sm.advance(PrayerType.OUR_FATHER)
    assert s.decade == 1
    assert s.bead == 0
    assert s.state == DecadeState.OUR_FATHER


def test_our_father_ignored_mid_decade(sm):
    sm.advance(PrayerType.OUR_FATHER)
    sm.advance(PrayerType.HAIL_MARY)
    s = sm.advance(PrayerType.OUR_FATHER)
    assert s.decade == 1
    assert s.state == DecadeState.HAIL_MARY


def test_our_father_ignored_from_complete(sm):
    for _ in range(5):
        _full_decade(sm)
    assert sm.get_state().state == DecadeState.COMPLETE
    s = sm.advance(PrayerType.OUR_FATHER)
    assert s.state == DecadeState.COMPLETE
    assert s.decade == 5


# ── Hail Mary ─────────────────────────────────────────────────────────────────

def test_hail_mary_first_bead(sm):
    sm.advance(PrayerType.OUR_FATHER)
    s = sm.advance(PrayerType.HAIL_MARY)
    assert s.bead == 1
    assert s.state == DecadeState.HAIL_MARY


def test_ten_hail_marys_reach_bead_10(sm):
    sm.advance(PrayerType.OUR_FATHER)
    for _ in range(10):
        s = sm.advance(PrayerType.HAIL_MARY)
    assert s.bead == 10
    assert s.state == DecadeState.HAIL_MARY


def test_hail_mary_capped_at_10(sm):
    sm.advance(PrayerType.OUR_FATHER)
    for _ in range(15):
        s = sm.advance(PrayerType.HAIL_MARY)
    assert s.bead == 10


def test_hail_mary_ignored_in_idle(sm):
    s = sm.advance(PrayerType.HAIL_MARY)
    assert s.state == DecadeState.IDLE
    assert s.bead == 0


# ── Glory Be ──────────────────────────────────────────────────────────────────

def test_glory_be_completes_decade(sm):
    sm.advance(PrayerType.OUR_FATHER)
    for _ in range(10):
        sm.advance(PrayerType.HAIL_MARY)
    s = sm.advance(PrayerType.GLORY_BE)
    assert s.state == DecadeState.GLORY_BE
    assert 1 in s.completed_decades


def test_glory_be_ignored_without_hail_marys(sm):
    sm.advance(PrayerType.OUR_FATHER)
    s = sm.advance(PrayerType.GLORY_BE)
    assert s.state == DecadeState.OUR_FATHER
    assert s.completed_decades == []


def test_glory_be_ignored_in_idle(sm):
    s = sm.advance(PrayerType.GLORY_BE)
    assert s.state == DecadeState.IDLE


# ── Fatima prayer ─────────────────────────────────────────────────────────────

def test_fatima_advances_from_glory_be(sm):
    sm.advance(PrayerType.OUR_FATHER)
    for _ in range(10):
        sm.advance(PrayerType.HAIL_MARY)
    sm.advance(PrayerType.GLORY_BE)
    s = sm.advance(PrayerType.FATIMA)
    assert s.state == DecadeState.FATIMA
    assert s.decade == 1


def test_our_father_accepted_after_fatima(sm):
    sm.advance(PrayerType.OUR_FATHER)
    for _ in range(10):
        sm.advance(PrayerType.HAIL_MARY)
    sm.advance(PrayerType.GLORY_BE)
    sm.advance(PrayerType.FATIMA)
    s = sm.advance(PrayerType.OUR_FATHER)
    assert s.decade == 2
    assert s.state == DecadeState.OUR_FATHER


def test_fatima_ignored_outside_glory_be(sm):
    sm.advance(PrayerType.OUR_FATHER)
    sm.advance(PrayerType.HAIL_MARY)
    s = sm.advance(PrayerType.FATIMA)
    assert s.state == DecadeState.HAIL_MARY  # unchanged


def test_fatima_skippable_our_father_directly_from_glory_be(sm):
    sm.advance(PrayerType.OUR_FATHER)
    for _ in range(10):
        sm.advance(PrayerType.HAIL_MARY)
    sm.advance(PrayerType.GLORY_BE)
    # Skip Fatima — Our Father directly starts next decade
    s = sm.advance(PrayerType.OUR_FATHER)
    assert s.decade == 2
    assert s.state == DecadeState.OUR_FATHER


def test_five_decades_with_fatima(sm):
    for decade in range(1, 6):
        sm.advance(PrayerType.OUR_FATHER)
        for _ in range(10):
            sm.advance(PrayerType.HAIL_MARY)
        sm.advance(PrayerType.GLORY_BE)
        if decade < 5:
            sm.advance(PrayerType.FATIMA)
    s = sm.get_state()
    assert s.state == DecadeState.COMPLETE
    assert len(s.completed_decades) == 5


# ── Multi-decade flow ─────────────────────────────────────────────────────────

def test_second_decade_starts_after_glory_be(sm):
    sm.advance(PrayerType.OUR_FATHER)
    for _ in range(10):
        sm.advance(PrayerType.HAIL_MARY)
    sm.advance(PrayerType.GLORY_BE)
    s = sm.advance(PrayerType.OUR_FATHER)
    assert s.decade == 2
    assert s.bead == 0
    assert s.state == DecadeState.OUR_FATHER


def test_five_decades_complete(sm):
    for _ in range(5):
        _full_decade(sm)
    s = sm.get_state()
    assert s.state == DecadeState.COMPLETE
    assert len(s.completed_decades) == 5


def test_completed_decades_recorded_correctly(sm):
    for _ in range(3):
        _full_decade(sm)
    assert sm.get_state().completed_decades == [1, 2, 3]


# ── Undo ──────────────────────────────────────────────────────────────────────

def test_undo_reverts_one_step(sm):
    sm.advance(PrayerType.OUR_FATHER)
    sm.undo()
    s = sm.get_state()
    assert s.state == DecadeState.IDLE
    assert s.decade == 0


def test_undo_multiple_steps(sm):
    sm.advance(PrayerType.OUR_FATHER)
    sm.advance(PrayerType.HAIL_MARY)
    sm.advance(PrayerType.HAIL_MARY)
    sm.undo()
    assert sm.get_state().bead == 1
    sm.undo()
    assert sm.get_state().bead == 0
    assert sm.get_state().state == DecadeState.OUR_FATHER


def test_undo_empty_history_returns_none(sm):
    assert sm.undo() is None


def test_undo_after_glory_be(sm):
    sm.advance(PrayerType.OUR_FATHER)
    for _ in range(10):
        sm.advance(PrayerType.HAIL_MARY)
    sm.advance(PrayerType.GLORY_BE)
    sm.undo()
    s = sm.get_state()
    assert s.state == DecadeState.HAIL_MARY
    assert s.bead == 10
    assert s.completed_decades == []


def test_reset_clears_history(sm):
    sm.advance(PrayerType.OUR_FATHER)
    sm.reset()
    assert sm.undo() is None


# ── Manual advance ────────────────────────────────────────────────────────────

def test_advance_manual_from_idle(sm):
    s = sm.advance_manual()
    assert s.state == DecadeState.OUR_FATHER
    assert s.decade == 1


def test_advance_manual_from_our_father(sm):
    sm.advance(PrayerType.OUR_FATHER)
    s = sm.advance_manual()
    assert s.state == DecadeState.HAIL_MARY
    assert s.bead == 1


def test_advance_manual_increments_hail_mary(sm):
    sm.advance(PrayerType.OUR_FATHER)
    for _ in range(5):
        sm.advance_manual()
    assert sm.get_state().bead == 5


def test_advance_manual_hail_mary_to_glory_be(sm):
    sm.advance(PrayerType.OUR_FATHER)
    for _ in range(10):
        sm.advance(PrayerType.HAIL_MARY)
    s = sm.advance_manual()
    assert s.state == DecadeState.GLORY_BE


def test_advance_manual_glory_be_to_fatima(sm):
    sm.advance(PrayerType.OUR_FATHER)
    for _ in range(10):
        sm.advance(PrayerType.HAIL_MARY)
    sm.advance(PrayerType.GLORY_BE)
    s = sm.advance_manual()
    assert s.state == DecadeState.FATIMA


def test_advance_manual_fatima_to_next_decade(sm):
    sm.advance(PrayerType.OUR_FATHER)
    for _ in range(10):
        sm.advance(PrayerType.HAIL_MARY)
    sm.advance(PrayerType.GLORY_BE)
    sm.advance(PrayerType.FATIMA)
    s = sm.advance_manual()
    assert s.state == DecadeState.OUR_FATHER
    assert s.decade == 2


def test_advance_manual_noop_at_complete(sm):
    for _ in range(5):
        _full_decade(sm)
    assert sm.get_state().state == DecadeState.COMPLETE
    s = sm.advance_manual()
    assert s.state == DecadeState.COMPLETE  # stays COMPLETE


def test_advance_manual_is_undoable(sm):
    sm.advance_manual()  # IDLE → OUR_FATHER
    sm.undo()
    assert sm.get_state().state == DecadeState.IDLE


# ── Edge cases ────────────────────────────────────────────────────────────────

def test_unknown_prayer_does_not_change_state(sm):
    sm.advance(PrayerType.OUR_FATHER)
    sm.advance(PrayerType.HAIL_MARY)
    before = sm.get_state().bead
    sm.advance(PrayerType.UNKNOWN)
    assert sm.get_state().bead == before
    assert sm.get_state().state == DecadeState.HAIL_MARY


def test_reset_clears_state(sm):
    sm.advance(PrayerType.OUR_FATHER)
    sm.advance(PrayerType.HAIL_MARY)
    sm.reset()
    s = sm.get_state()
    assert s.decade == 0
    assert s.bead == 0
    assert s.state == DecadeState.IDLE
    assert s.completed_decades == []
    assert s.last_prayer is None


def test_last_prayer_recorded(sm):
    sm.advance(PrayerType.OUR_FATHER)
    assert sm.get_state().last_prayer == PrayerType.OUR_FATHER
    sm.advance(PrayerType.HAIL_MARY)
    assert sm.get_state().last_prayer == PrayerType.HAIL_MARY


# ── to_dict ───────────────────────────────────────────────────────────────────

def test_to_dict_structure(sm):
    sm.advance(PrayerType.OUR_FATHER)
    d = sm.get_state().to_dict()
    assert d["decade"] == 1
    assert d["bead"] == 0
    assert d["state"] == "OUR_FATHER"
    assert d["last_prayer"] == "OUR_FATHER"
    assert d["completed_decades"] == []


def test_to_dict_no_last_prayer(sm):
    d = sm.get_state().to_dict()
    assert d["last_prayer"] is None


def test_to_dict_fatima_state(sm):
    sm.advance(PrayerType.OUR_FATHER)
    for _ in range(10):
        sm.advance(PrayerType.HAIL_MARY)
    sm.advance(PrayerType.GLORY_BE)
    sm.advance(PrayerType.FATIMA)
    d = sm.get_state().to_dict()
    assert d["state"] == "FATIMA"
    assert d["last_prayer"] == "FATIMA"
