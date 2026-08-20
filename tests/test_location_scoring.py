"""Tests for the generalized (profile-driven) location matching."""
from core.scorer import check_location_friendly
from core.profile import validate_config

PROFILE = {
    "location": {
        "location_positive": ["croatia", "europe", "emea"],
        "location_negative": ["us only", "us citizen"],
        "timezone_compatible": ["cet", "utc"],
        "timezone_incompatible": ["pst only"],
    }
}


def test_positive_keyword_matches():
    r = check_location_friendly("Remote - Europe", "", profile=PROFILE)
    assert r["result"] == "yes"


def test_negative_keyword_blocks():
    r = check_location_friendly("Remote", "US citizen required", profile=PROFILE)
    assert r["result"] == "no"


def test_timezone_incompatible_blocks():
    r = check_location_friendly("Remote", "core hours PST only", profile=PROFILE)
    assert r["result"] == "no"


def test_global_remote_is_yes():
    r = check_location_friendly("Remote", "work from anywhere", profile=PROFILE)
    assert r["result"] == "yes"


def test_compatible_timezone_is_maybe():
    r = check_location_friendly("Remote", "overlap with UTC hours", profile=PROFILE)
    assert r["result"] == "maybe"


def test_unspecified_remote_is_maybe():
    r = check_location_friendly("Remote", "great team", profile=PROFILE)
    assert r["result"] == "maybe"


def test_no_hardcoded_india_bias():
    r = check_location_friendly("Bangalore, India", "", profile=PROFILE)
    assert r["result"] == "maybe"  # not an automatic yes anymore


def test_legacy_india_keys_migrate():
    cfg = validate_config({"location": {"india_positive": ["india"],
                                        "india_negative": ["us only"]}})
    assert cfg["location"]["location_positive"] == ["india"]
    assert cfg["location"]["location_negative"] == ["us only"]
    assert "india_positive" not in cfg["location"]
