"""JSearch via RapidAPI — aggregates jobs from LinkedIn, Indeed, Glassdoor, ZipRecruiter, Google Jobs.
Free tier: 200 requests/month (each request returns 10 jobs).
Docs: https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch
"""

import httpx
from sources.base import BaseSource
from core.models import Job
from config.settings import RAPIDAPI_KEY
from core.database import log_api_call


class JSearchSource(BaseSource):
    name = "jsearch"
    # v2: the old /search endpoint was removed (404s). v2 nests results under
    # data.jobs, ignores remote_jobs_only, and returns 0 results when the word
    # "remote" appears in the query text — see _clean_params.
    BASE_URL = "https://jsearch.p.rapidapi.com/search-v2"

    @staticmethod
    def _clean_params(q: dict) -> dict:
        params = {k: v for k, v in q.items() if k != "remote_jobs_only"}
        params["query"] = " ".join(
            w for w in str(params.get("query", "")).split() if w.lower() != "remote"
        )
        return params

    @staticmethod
    def _extract_items(data: dict) -> list:
        payload = data.get("data")
        if isinstance(payload, dict):  # v2 shape
            return payload.get("jobs") or []
        return payload or []  # legacy v1 shape (list)

    def __init__(self, queries: list[dict] = None):
        # Queries are now sourced from the DB (search_queries table), which is
        # seeded per profile on activation / preset import. If the caller passes
        # nothing, this source is a no-op (returns empty list from fetch()).
        self.queries = queries or []
        self.api_key = RAPIDAPI_KEY

    async def fetch(self) -> list[Job]:
        if not self.api_key:
            return []

        headers = {
            "x-rapidapi-host": "jsearch.p.rapidapi.com",
            "x-rapidapi-key": self.api_key,
        }

        all_jobs = []
        async with httpx.AsyncClient(timeout=60) as client:
            for q in self.queries:
                try:
                    params = {**self._clean_params(q), "page": 1, "num_pages": 1, "employment_types": "FULLTIME"}
                    resp = await client.get(self.BASE_URL, headers=headers, params=params)
                    success = resp.status_code == 200
                    log_api_call("jsearch", success=success, notes=q.get("query", ""))
                    if not success:
                        print(
                            f"  [jsearch] '{params['query']}' → HTTP {resp.status_code}: {resp.text[:150]}",
                            flush=True,
                        )
                        continue
                    data = resp.json()
                    items = self._extract_items(data)
                    print(
                        f"  [jsearch] '{params['query']}' ({params.get('country', '?')}) "
                        f"→ HTTP {resp.status_code}, {len(items)} jobs",
                        flush=True,
                    )
                    for item in items:
                        # v2 ignores the remote_jobs_only param, so enforce it
                        # client-side via the per-job remote flag.
                        if q.get("remote_jobs_only") and not item.get("job_is_remote"):
                            continue
                        job = self._map_job(item)
                        if job:
                            all_jobs.append(job)
                except Exception as e:
                    log_api_call("jsearch", success=False, notes=str(e)[:100])
                    continue

        return all_jobs

    def _map_job(self, item: dict) -> Job:
        location_parts = [
            item.get("job_city", ""),
            item.get("job_state", ""),
            item.get("job_country", ""),
        ]
        location = ", ".join(p for p in location_parts if p) or "Remote"
        if item.get("job_is_remote"):
            location = "Remote" if not location_parts[0] else f"Remote / {location}"

        salary = ""
        if item.get("job_min_salary") and item.get("job_max_salary"):
            period = item.get("job_salary_period", "year").lower()
            salary = f"${item['job_min_salary']:,} - ${item['job_max_salary']:,} / {period}"

        # Apply URL — prefer official apply link
        url = item.get("job_apply_link", "") or item.get("job_google_link", "")

        # Extract company domain from apply link
        domain = ""
        employer_website = item.get("employer_website", "")
        if employer_website:
            domain = employer_website.replace("https://", "").replace("http://", "").replace("www.", "").rstrip("/")

        return Job(
            title=item.get("job_title", ""),
            company=item.get("employer_name", ""),
            location=location,
            description=item.get("job_description", "")[:5000],  # truncate huge descriptions
            url=url,
            source="jsearch",
            posted_date=item.get("job_posted_at_datetime_utc", "") or item.get("job_posted_at", ""),
            company_domain=domain,
            salary=salary,
            job_type=item.get("job_employment_type", "FULLTIME").lower(),
        )
