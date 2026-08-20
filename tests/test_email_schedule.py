"""Tests for the multi-send email schedule config."""
from config.settings import parse_email_hours


def test_parses_comma_separated_hours():
    assert parse_email_hours("9,14,19") == [9, 14, 19]


def test_empty_string_falls_back_to_single_hour():
    assert parse_email_hours("", fallback=9) == [9]


def test_whitespace_and_sorting():
    assert parse_email_hours(" 19 , 9 ,14") == [9, 14, 19]


def test_ignores_invalid_and_out_of_range_values():
    assert parse_email_hours("abc,25,-1,14", fallback=9) == [14]


def test_all_invalid_falls_back():
    assert parse_email_hours("abc,99", fallback=7) == [7]


def test_deduplicates():
    assert parse_email_hours("9,9,14") == [9, 14]
