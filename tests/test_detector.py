"""Tests for the PrayerDetector."""

import time

import pytest

from detector import PrayerDetector
from rosary_state import PrayerType


@pytest.fixture()
def det():
    """Detector with zero cooldown for isolated unit tests."""
    return PrayerDetector(threshold=1, cooldown=0.0)


# ── Basic detection ───────────────────────────────────────────────────────────

def test_detect_hail_mary(det):
    assert det.detect("Hail Mary full of grace the Lord is with thee") == PrayerType.HAIL_MARY


def test_detect_hail_mary_partial_phrase(det):
    assert det.detect("blessed art thou among women") == PrayerType.HAIL_MARY


def test_detect_our_father(det):
    assert det.detect("Our Father who art in heaven hallowed be thy name") == PrayerType.OUR_FATHER


def test_detect_our_father_daily_bread(det):
    assert det.detect("give us this day our daily bread") == PrayerType.OUR_FATHER


def test_detect_glory_be(det):
    assert det.detect("Glory be to the Father and to the Son world without end") == PrayerType.GLORY_BE


def test_detect_glory_be_partial(det):
    # Text containing individual Glory Be words but no complete anchor phrase
    assert det.detect("now and ever shall be world without") is None


def test_detect_fatima(det):
    assert det.detect("O my Jesus forgive us our sins") == PrayerType.FATIMA


def test_detect_unknown_returns_none(det):
    assert det.detect("hello how are you doing today") is None


def test_empty_transcript_returns_none(det):
    assert det.detect("") is None


def test_none_like_whitespace_returns_none(det):
    assert det.detect("   ") is None


# ── Case insensitivity ────────────────────────────────────────────────────────

def test_case_insensitive_upper(det):
    assert det.detect("HAIL MARY FULL OF GRACE") == PrayerType.HAIL_MARY


def test_case_insensitive_mixed(det):
    assert det.detect("Our Father WHO ART in heaven") == PrayerType.OUR_FATHER


# ── Threshold ─────────────────────────────────────────────────────────────────

def test_threshold_2_requires_2_anchors():
    d = PrayerDetector(threshold=2, cooldown=0.0)
    # Two anchors present
    result = d.detect("Hail Mary full of grace blessed art thou among women")
    assert result == PrayerType.HAIL_MARY


def test_threshold_2_single_anchor_fails():
    d = PrayerDetector(threshold=2, cooldown=0.0)
    # Only one anchor present
    assert d.detect("Hail Mary") is None


def test_threshold_3_requires_3_anchors():
    d = PrayerDetector(threshold=3, cooldown=0.0)
    text = "hail mary full of grace blessed art thou among women mother of god"
    assert d.detect(text) == PrayerType.HAIL_MARY


# ── Cooldown ──────────────────────────────────────────────────────────────────

def test_cooldown_blocks_immediate_repeat():
    d = PrayerDetector(threshold=1, cooldown=60.0)
    first  = d.detect("Hail Mary full of grace")
    second = d.detect("Hail Mary full of grace")
    assert first  == PrayerType.HAIL_MARY
    assert second is None


def test_cooldown_does_not_block_different_prayer():
    d = PrayerDetector(threshold=1, cooldown=60.0)
    d.detect("Hail Mary full of grace")
    result = d.detect("Our Father who art in heaven")
    assert result == PrayerType.OUR_FATHER


def test_cooldown_expires():
    d = PrayerDetector(threshold=1, cooldown=0.05)
    d.detect("Hail Mary full of grace")
    time.sleep(0.1)
    assert d.detect("Hail Mary full of grace") == PrayerType.HAIL_MARY


def test_reset_cooldowns_allows_redetection():
    d = PrayerDetector(threshold=1, cooldown=999.0)
    d.detect("Hail Mary full of grace")
    d.reset_cooldowns()
    assert d.detect("Hail Mary full of grace") == PrayerType.HAIL_MARY


# ── Best-match selection ──────────────────────────────────────────────────────

def test_best_match_wins_on_anchor_count(det):
    # Hail Mary has more anchors in this text than any other prayer
    text = "hail mary full of grace blessed art thou among women holy mary mother of god"
    assert det.detect(text) == PrayerType.HAIL_MARY


def test_our_father_beats_weak_overlap(det):
    # Strong Our Father signal; Glory Be only gets one incidental word
    text = "our father who art in heaven hallowed be thy name thy kingdom come thy will be done"
    assert det.detect(text) == PrayerType.OUR_FATHER


# ── _score_transcript (internal) ─────────────────────────────────────────────

def test_score_transcript_empty(det):
    assert det._score_transcript("") == {}


def test_score_transcript_counts_anchors(det):
    scores = det._score_transcript("hail mary full of grace the lord is with thee")
    assert scores.get(PrayerType.HAIL_MARY, 0) >= 3
