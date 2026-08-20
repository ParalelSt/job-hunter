"""Tests for the collect-on-startup staleness check."""
from datetime import datetime, timedelta

from core.collector import startup_collect_due

NOW = datetime(2026, 8, 6, 12, 0, 0)


def test_never_collected_is_due():
    assert startup_collect_due(None, NOW, 6) is True
    assert startup_collect_due("", NOW, 6) is True


def test_recent_collection_is_not_due():
    last = (NOW - timedelta(hours=1)).isoformat()
    assert startup_collect_due(last, NOW, 6) is False


def test_stale_collection_is_due():
    last = (NOW - timedelta(hours=7)).isoformat()
    assert startup_collect_due(last, NOW, 6) is True


def test_exact_gap_boundary_is_due():
    last = (NOW - timedelta(hours=6)).isoformat()
    assert startup_collect_due(last, NOW, 6) is True


def test_malformed_timestamp_is_due():
    assert startup_collect_due("not-a-date", NOW, 6) is True


def test_zero_gap_always_due():
    last = NOW.isoformat()
    assert startup_collect_due(last, NOW, 0) is True
