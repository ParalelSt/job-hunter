"""Tests for JSearch v2 endpoint adaptations (no network calls)."""
from sources.jsearch import JSearchSource


def test_clean_params_strips_remote_word():
    p = JSearchSource._clean_params({"query": "ai engineer remote", "country": "US"})
    assert p["query"] == "ai engineer"


def test_clean_params_drops_remote_jobs_only():
    p = JSearchSource._clean_params({"query": "ai engineer", "remote_jobs_only": True})
    assert "remote_jobs_only" not in p


def test_clean_params_keeps_other_fields():
    p = JSearchSource._clean_params({"query": "llm engineer", "country": "HR", "date_posted": "week"})
    assert p == {"query": "llm engineer", "country": "HR", "date_posted": "week"}


def test_extract_items_v2_shape():
    assert JSearchSource._extract_items({"data": {"jobs": [{"a": 1}], "cursor": "x"}}) == [{"a": 1}]


def test_extract_items_legacy_list_shape():
    assert JSearchSource._extract_items({"data": [{"a": 1}]}) == [{"a": 1}]


def test_remote_only_filter_drops_onsite_jobs():
    import asyncio
    from unittest.mock import patch, MagicMock

    src = JSearchSource(queries=[{"query": "ai engineer", "remote_jobs_only": True}])
    src.api_key = "fake"
    resp = MagicMock(status_code=200)
    resp.json.return_value = {"data": {"jobs": [
        {"job_title": "Remote AI Eng", "employer_name": "A", "job_is_remote": True},
        {"job_title": "Onsite AI Eng", "employer_name": "B", "job_is_remote": False},
    ]}}

    class FakeClient:
        async def __aenter__(self): return self
        async def __aexit__(self, *a): return False
        async def get(self, *a, **k): return resp

    with patch("sources.jsearch.httpx.AsyncClient", return_value=FakeClient()), \
         patch("sources.jsearch.log_api_call"):
        jobs = asyncio.run(src.fetch())
    assert [j.title for j in jobs] == ["Remote AI Eng"]


def test_extract_items_empty():
    assert JSearchSource._extract_items({}) == []
    assert JSearchSource._extract_items({"data": {"jobs": None}}) == []
