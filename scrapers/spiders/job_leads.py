# import base64
# import json
# import time
# from typing import Any, Dict, Generator, Iterable, Optional, Tuple
#
# from curl_cffi import requests
#
#
# def _jwt_payload(token: str) -> dict:
#     """Decode JWT payload without verifying signature (for exp only)."""
#     try:
#         payload_b64 = token.split(".")[1]
#         payload_b64 += "=" * (-len(payload_b64) % 4)
#         return json.loads(base64.urlsafe_b64decode(payload_b64).decode("utf-8"))
#     except Exception:
#         return {}
#
#
# class JobleadsClient:
#     """
#     JobLeads client using curl_cffi with auto login + auto token refresh.
#     NOTE: JobLeads uses split token cookies:
#       - jwt_hp = header.payload
#       - jwt_s  = signature
#     Bearer token must be: f"{jwt_hp}.{jwt_s}"
#     """
#
#     def __init__(self, email: str, password: str, impersonate: str = "chrome124"):
#         self.email = email
#         self.password = password
#         self.impersonate = impersonate
#         self.s = requests.Session()
#
#         self.token: Optional[str] = None
#         self.exp: int = 0  # epoch seconds
#
#     def login_and_get_token(self) -> str:
#         url = "https://www.jobleads.com/user/login/form"
#
#         boundary = "----WebKitFormBoundary6QwfUhHc0phBQ9U6"
#         body = (
#             f"--{boundary}\r\n"
#             f'Content-Disposition: form-data; name="email"\r\n\r\n{self.email}\r\n'
#             f"--{boundary}\r\n"
#             f'Content-Disposition: form-data; name="password"\r\n\r\n{self.password}\r\n'
#             f"--{boundary}\r\n"
#             f'Content-Disposition: form-data; name="autoLogin"\r\n\r\n0\r\n'
#             f"--{boundary}\r\n"
#             f'Content-Disposition: form-data; name="redirectBackUrl"\r\n\r\n/home\r\n'
#             f"--{boundary}--\r\n"
#         )
#
#         headers = {
#             "accept": "application/json, text/plain, */*",
#             "accept-language": "en-US,en;q=0.9",
#             "origin": "https://www.jobleads.com",
#             "referer": "https://www.jobleads.com/",
#             "user-agent": "Mozilla/5.0",
#             "x-requested-with": "XMLHttpRequest",
#             "content-type": f"multipart/form-data; boundary={boundary}",
#         }
#
#         r = self.s.post(
#             url,
#             headers=headers,
#             data=body,
#             impersonate=self.impersonate,
#         )
#         r.raise_for_status()
#
#         hp = self.s.cookies.get("jwt_hp")
#         sig = self.s.cookies.get("jwt_s")
#
#         if not hp or not sig:
#             print("cookie keys:", list(self.s.cookies.keys()))
#             raise RuntimeError("Login OK but jwt_hp/jwt_s missing")
#
#         return f"{hp}.{sig}"
#
#     def refresh_if_needed(self, skew_seconds: int = 120) -> None:
#         """
#         Refreshes token if:
#           - no token yet
#           - current time >= exp - skew_seconds
#         """
#         if not self.token or time.time() >= (self.exp - skew_seconds):
#             new_token = self.login_and_get_token()
#             payload = _jwt_payload(new_token)
#             self.token = new_token
#             self.exp = int(payload.get("exp", 0)) or 0
#
#     def request(self, method: str, url: str, *, headers: Optional[dict] = None, retry: bool = True, **kwargs):
#         self.refresh_if_needed()
#
#         hdrs = dict(headers or {})
#         hdrs["authorization"] = f"Bearer {self.token}"
#
#         resp = self.s.request(
#             method,
#             url,
#             headers=hdrs,
#             impersonate=self.impersonate,
#             **kwargs,
#         )
#
#         # If server says token invalid/expired, re-login once & retry
#         if retry and resp.status_code in (401, 403):
#             self.token = None
#             self.exp = 0
#             self.refresh_if_needed(skew_seconds=0)
#
#             hdrs["authorization"] = f"Bearer {self.token}"
#             resp = self.s.request(
#                 method,
#                 url,
#                 headers=hdrs,
#                 impersonate=self.impersonate,
#                 **kwargs,
#             )
#
#         return resp
#
#
# def _extract_jobs_list(data: Dict[str, Any]) -> list:
#     """
#     Try common keys for job list.
#     If your response uses a different structure, adjust here once.
#     """
#     if isinstance(data.get("jobs"), list):
#         return data["jobs"]
#     if isinstance(data.get("results"), list):
#         return data["results"]
#     if isinstance(data.get("resultList"), list):
#         return data["resultList"]
#     if isinstance(data.get("data"), dict) and isinstance(data["data"].get("jobs"), list):
#         return data["data"]["jobs"]
#     return []
#
#
# def iter_search_pages(
#     client: JobleadsClient,
#     base_payload: Dict[str, Any],
#     headers: Dict[str, str],
#     page_size: int = 25,
#     max_pages: Optional[int] = None,
# ) -> Generator[Tuple[int, Dict[str, Any], list], None, None]:
#     """
#     Yields (page_index, response_json, jobs_list).
#     Pagination is driven by:
#       - startIndex (offset)
#       - limit (page size)
#     """
#     payload = dict(base_payload)
#     payload["limit"] = page_size
#
#     start = int(payload.get("startIndex", 0))
#     page = 0
#
#     while True:
#         if max_pages is not None and page >= max_pages:
#             break
#
#         payload["startIndex"] = start
#
#         resp = client.request(
#             "POST",
#             "https://www.jobleads.com/api/v2/search/v2",
#             headers=headers,
#             json=payload,
#         )
#         resp.raise_for_status()
#         data = resp.json()
#
#         jobs = _extract_jobs_list(data)
#
#         yield page, data, jobs
#
#         # Stop if no more jobs
#         if not jobs:
#             break
#
#         got = len(jobs)
#         start += got
#         page += 1
#
#         # If fewer than requested returned, likely last page
#         if got < page_size:
#             break
#
#
# def iter_search_jobs(
#     client: JobleadsClient,
#     base_payload: Dict[str, Any],
#     headers: Dict[str, str],
#     page_size: int = 25,
#     max_pages: Optional[int] = None,
# ) -> Generator[Dict[str, Any], None, None]:
#     """Yields each job dict across all pages."""
#     for _, _, jobs in iter_search_pages(client, base_payload, headers, page_size=page_size, max_pages=max_pages):
#         for j in jobs:
#             yield j
#
#
# if __name__ == "__main__":
#     # -------------------------
#     # Client
#     # -------------------------
#     client = JobleadsClient(
#         email="berapec475@ixunbo.com",
#         password="Berapec475@ixunbo.com",
#         impersonate="chrome124",
#     )
#
#     # -------------------------
#     # Headers for search API
#     # (Keep referer matching search page - helps)
#     # -------------------------
#     search_headers = {
#         "accept": "application/json, text/plain, */*",
#         "accept-language": "en-US,en;q=0.9",
#         "content-type": "application/json",
#         "origin": "https://www.jobleads.com",
#         "referer": "https://www.jobleads.com/search/jobs?keywords=python&location=&location_country=NLD&minSalary=40000&maxSalary=-1",
#         "user-agent": "Mozilla/5.0",
#         "x-requested-with": "XMLHttpRequest",
#     }
#
#     # -------------------------
#     # Base payload (first page)
#     # -------------------------
#     payload = {
#         "keywords": "python",
#         "location": "",
#         "country": "NLD",
#         "radius": 0,
#         "minSalary": 40000,
#         "maxSalary": -1,
#         "initialSearchId": 0,
#         "refinedSearchId": 0,
#         "lastExecutedSearch": None,
#         "searchFiltering": 0,
#         "featuredJobs": "",
#         "origin": 1,
#         "savedSearchId": None,
#         "startIndex": 0,   # offset
#         "limit": 25,       # page size (will be overwritten by page_size in paginator)
#         "filters": {},
#     }
#
#     # -------------------------
#     # Option A: page-by-page
#     # -------------------------
#     print("=== PAGES ===")
#     for page_idx, data, jobs in iter_search_pages(
#         client,
#         payload,
#         search_headers,
#         page_size=25,
#         max_pages=5,  # change/remove as needed
#     ):
#         print(f"Page {page_idx} -> jobs={len(jobs)}")
#         # print("Top-level keys:", list(data.keys()))
#
#     # -------------------------
#     # Option B: job-by-job
#     # -------------------------
#     print("\n=== JOBS (first 50) ===")
#     count = 0
#     for job in iter_search_jobs(
#         client,
#         payload,
#         search_headers,
#         page_size=25,
#         max_pages=None,
#     ):
#         # Try common fields (depends on response)
#         title = job.get("title") or job.get("jobTitle") or job.get("name")
#         jid = job.get("id") or job.get("jobId") or job.get("uuid")
#         print(jid, "-", title)
#         count += 1
#         if count >= 50:
#             break


import base64
import json
import time
from typing import Dict, Any, Generator, Optional
from curl_cffi import requests


# -------------------------------------------------------------------
# JWT helpers
# -------------------------------------------------------------------

def _jwt_payload(token: str) -> dict:
    """Decode JWT payload (no signature verification, exp only)."""
    try:
        payload_b64 = token.split(".")[1]
        payload_b64 += "=" * (-len(payload_b64) % 4)
        return json.loads(base64.urlsafe_b64decode(payload_b64))
    except Exception:
        return {}


# -------------------------------------------------------------------
# Client
# -------------------------------------------------------------------

class JobleadsClient:
    """
    JobLeads client with:
    - login
    - split JWT handling (jwt_hp + jwt_s)
    - auto refresh
    """

    def __init__(self, email: str, password: str, impersonate="chrome124"):
        self.email = email
        self.password = password
        self.impersonate = impersonate
        self.s = requests.Session()

        self.token: Optional[str] = None
        self.exp: int = 0

    # -----------------------------
    # Login
    # -----------------------------
    def login_and_get_token(self) -> str:
        url = "https://www.jobleads.com/user/login/form"
        boundary = "----WebKitFormBoundary6QwfUhHc0phBQ9U6"

        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="email"\r\n\r\n{self.email}\r\n'
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="password"\r\n\r\n{self.password}\r\n'
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="autoLogin"\r\n\r\n0\r\n'
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="redirectBackUrl"\r\n\r\n/home\r\n'
            f"--{boundary}--\r\n"
        )

        headers = {
            "accept": "application/json, text/plain, */*",
            "origin": "https://www.jobleads.com",
            "referer": "https://www.jobleads.com/",
            "user-agent": "Mozilla/5.0",
            "x-requested-with": "XMLHttpRequest",
            "content-type": f"multipart/form-data; boundary={boundary}",
        }

        r = self.s.post(
            url,
            headers=headers,
            data=body,
            impersonate=self.impersonate,
        )
        r.raise_for_status()

        hp = self.s.cookies.get("jwt_hp")
        sig = self.s.cookies.get("jwt_s")

        if not hp or not sig:
            raise RuntimeError("Login OK but jwt_hp / jwt_s missing")

        return f"{hp}.{sig}"

    # -----------------------------
    # Token refresh
    # -----------------------------
    def refresh_if_needed(self, skew_seconds: int = 120):
        if not self.token or time.time() >= (self.exp - skew_seconds):
            self.token = self.login_and_get_token()
            payload = _jwt_payload(self.token)
            self.exp = int(payload.get("exp", 0))

    # -----------------------------
    # Authenticated request
    # -----------------------------
    def request(self, method: str, url: str, *, headers=None, retry=True, **kwargs):
        self.refresh_if_needed()

        hdrs = dict(headers or {})
        hdrs["authorization"] = f"Bearer {self.token}"

        r = self.s.request(
            method,
            url,
            headers=hdrs,
            impersonate=self.impersonate,
            **kwargs,
        )

        if retry and r.status_code in (401, 403):
            self.token = None
            self.exp = 0
            self.refresh_if_needed(0)
            hdrs["authorization"] = f"Bearer {self.token}"

            r = self.s.request(
                method,
                url,
                headers=hdrs,
                impersonate=self.impersonate,
                **kwargs,
            )

        return r

    def get_job_details(
            self,
            job_id: str,
            locale: str = "en_PK",
            language: str = "en",
    ) -> dict:
        """
        Fetch full job details by job ID.
        """

        url = (
            f"https://www.jobleads.com/api/v3/job/detailsForAppNew/"
            f"{locale}/{job_id}?language={language}"
        )

        headers = {
            "accept": "application/json, text/plain, */*",
            "origin": "https://www.jobleads.com",
            "referer": "https://www.jobleads.com/search/jobs",
            "x-requested-with": "XMLHttpRequest",
            "user-agent": "Mozilla/5.0",
        }

        r = self.request(
            "GET",
            url,
            headers=headers,
        )
        r.raise_for_status()
        return r.json()

    def get_job_facet(
            self,
            job_id: str,
            locale: str = "en_PK",
            language: str = "en",
    ) -> dict:
        """
        Fetch full job details by job ID.
        """

        url = (
            f"https://www.jobleads.com/api/v3/job/detailsForAppNew/"
            f"{locale}/{job_id}?language={language}"
        )

        headers = {
            "accept": "application/json, text/plain, */*",
            "origin": "https://www.jobleads.com",
            "referer": "https://www.jobleads.com/search/jobs",
            "x-requested-with": "XMLHttpRequest",
            "user-agent": "Mozilla/5.0",
        }

        r = self.request(
            "GET",
            url,
            headers=headers,
        )
        r.raise_for_status()
        return r.json()

    # ---------------------------------
    # Fetch Canonical Job HTML Page
    # ---------------------------------
    def fetch_job_page_html(self, canonical_url: str) -> str:
        """
        Fetch public SSR HTML page for a job.
        No auth required.
        """

        r = requests.get(
            canonical_url,
            headers={
                "user-agent": "Mozilla/5.0",
                "accept": "text/html",
            },
            timeout=30,
        )
        r.raise_for_status()
        print(r.text)
        return r.text

    def extract_jobposting_jsonld(self,html_text: str) -> dict:
        soup = BeautifulSoup(html_text, "lxml")
        script = soup.find("script", {"type": "application/ld+json", "id": "jobPostingLdjson"})
        if not script or not script.string:
            raise ValueError("JobPosting JSON-LD not found")
        return json.loads(script.string.strip())

    def normalize_jobposting(self, data: dict) -> dict:
        # description is HTML (escaped inside JSON)
        desc_html = data.get("description")

        return {
            "job_id": (data.get("identifier") or {}).get("value"),
            "title": data.get("title"),
            "company": (data.get("hiringOrganization") or {}).get("name"),
            "employment_type": data.get("employmentType"),
            "date_posted": data.get("datePosted"),
            "valid_through": data.get("validThrough"),
            "location": {
                "city": (((data.get("jobLocation") or {}).get("address") or {}).get("addressLocality")),
                "region": (((data.get("jobLocation") or {}).get("address") or {}).get("addressRegion")),
                "country": (((data.get("jobLocation") or {}).get("address") or {}).get("addressCountry")),
            },
            "salary": {
                "currency": data.get("salaryCurrency"),
                "min": (((data.get("baseSalary") or {}).get("value") or {}).get("minValue")),
                "max": (((data.get("baseSalary") or {}).get("value") or {}).get("maxValue")),
                "unit": (((data.get("baseSalary") or {}).get("value") or {}).get("unitText")),
            },
            "description_html": desc_html,
        }

    def find_first(self, d, keys):
        """Try multiple keys in dict, return first found non-empty."""
        for k in keys:
            v = d.get(k)
            if v:
                return v
        return None


# -------------------------------------------------------------------
# Classic Search (pagination)
# -------------------------------------------------------------------

def iter_classic_search(
    client: JobleadsClient,
    payload: Dict[str, Any],
    headers: Dict[str, str],
    page_size: int = 25,
) -> Generator[dict, None, None]:

    start = 0
    while True:
        payload["startIndex"] = start
        payload["limit"] = page_size

        r = client.request(
            "POST",
            "https://www.jobleads.com/api/v2/search/v2",
            headers=headers,
            json=payload,
        )
        r.raise_for_status()
        data = r.json()

        jobs = data.get("jobs") or data.get("results") or []
        if not jobs:
            break

        for job in jobs:
            yield job

        if len(jobs) < page_size:
            break

        start += len(jobs)


# -------------------------------------------------------------------
# Semantic (VDB) Search
# -------------------------------------------------------------------

def semantic_search(
    client: JobleadsClient,
    keywords: list[str],
    country_alpha2: str,
    min_salary: int,
    valid_from_ts: int,
    limit: int = 100,
) -> dict:

    payload = {
        "keywords": keywords,
        "filters": [
            {
                "key": "location",
                "operator": "eq",
                "value": [{"alpha2Country": country_alpha2, "names": []}],
            },
            {"key": "minSalary", "operator": "gte", "value": min_salary},
            {"key": "validFrom", "operator": "gte", "value": valid_from_ts},
        ],
        "limit": limit,
        "engineOptions": {
            "engineType": "vdbSearch"
        },
    }

    headers = {
        "accept": "application/json, text/plain, */*",
        "content-type": "application/json",
        "origin": "https://www.jobleads.com",
        "referer": "https://www.jobleads.com/search/jobs",
        "x-requested-with": "XMLHttpRequest",
        "x-search-context": "web_ui",
        "x-search-trigger": "manual",
        "user-agent": "Mozilla/5.0",
    }

    r = client.request(
        "POST",
        "https://www.jobleads.com/job-search/search",
        headers=headers,
        json=payload,
    )
    r.raise_for_status()
    return r.json()





# -------------------------------------------------------------------
# Example usage
# -------------------------------------------------------------------
import base64
import json
import time
from urllib.parse import urljoin

import scrapy
from bs4 import BeautifulSoup
from curl_cffi import requests

# if __name__ == "__main__":
#     client = JobleadsClient(
#         email="berapec475@ixunbo.com",
#         password="Berapec475@ixunbo.com",
#     )
#
#     # ---------- Classic Search ----------
#     classic_headers = {
#         "accept": "application/json, text/plain, */*",
#         "content-type": "application/json",
#         "origin": "https://www.jobleads.com",
#         "referer": "https://www.jobleads.com/search/jobs?keywords=python",
#         "x-requested-with": "XMLHttpRequest",
#         "user-agent": "Mozilla/5.0",
#     }
#
#     classic_payload = {
#         "keywords": "python",
#         "location": "",
#         "country": "NLD",
#         "radius": 0,
#         "minSalary": 40000,
#         "maxSalary": -1,
#         "initialSearchId": 0,
#         "refinedSearchId": 0,
#         "lastExecutedSearch": None,
#         "searchFiltering": 0,
#         "featuredJobs": "",
#         "origin": 1,
#         "savedSearchId": None,
#         "startIndex": 0,
#         "limit": 25,
#         "filters": {},
#     }
#
#     # print("=== CLASSIC SEARCH ===")
#     # for job in iter_classic_search(client, classic_payload, classic_headers):
#     #     print(job.get("id"), job.get("title"))
#     #
#     # # ---------- Semantic Search ----------
#     # print("\n=== SEMANTIC SEARCH ===")
#     # semantic_result = semantic_search(
#     #     client,
#     #     keywords=["python"],
#     #     country_alpha2="NL",
#     #     min_salary=40000,
#     #     valid_from_ts=1769764856,
#     #     limit=100,
#     # )
#     #
#     # print(json.dumps(semantic_result, indent=2)[:1500])
#
#
#
#
#     job_id = "ee309af7f1f24849f11fcbc23692b7c7a"
#
#     details = client.get_job_details(job_id)
#     print(json.dumps(details, indent=2))
#     job_content = details.get('payload',{}).get('content',{})
#     canonical_url = job_content.get('canonicalUrl',"")
#     _url = f"https://www.jobleads.com/{canonical_url.lstrip('/')}"
#     # canonical_url = "https://www.jobleads.com/nl/job/python-developer--amsterdam--eeaccebf11c0e0a0445a8c9b860a03f22"
#     _scraped_page = client.fetch_job_page_html(_url)
#     jsonld = client.extract_jobposting_jsonld(_scraped_page)
#     normalized = client.normalize_jobposting(jsonld)
#     job_content['job_description'] = normalized
#     print(normalized)
#
#
#
#
#     """
#     ✅ What you now have
# 	•	🔐 Correct split-JWT auth (browser-accurate)
# 	•	🔁 Auto refresh
# 	•	📄 Classic paginated search
# 	•	🧠 Semantic / vector (VDB) search
# 	•	🧱 Clean separation of concerns
# 	•	🚀 Ready for scale / scraping / pipelines
#
# ⸻
#
# If you want next:
# 	•	unify both searches into one merged result set
# 	•	deduplicate classic vs semantic jobs
# 	•	async / parallel searches
# 	•	export to DB / CSV / Parquet
#     """
#
#
#     # -----------------------------
#     # Job Detail API
#     # -----------------------------
#
#
#
#     # job_id = "ee309af7f1f24849f11fcbc23692b7c7a"
#     #
#     # details = client.get_job_details(job_id)
#     #
#     # print(json.dumps(details, indent=2))

if __name__ == '__main__':


    url = 'https://www.jobleads.com/api/v1/search/keyword-recommendation/en_PK/python/NLD'

    headers = {
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'priority': 'u=1, i',
        'referer': 'https://www.jobleads.com/search/jobs',
        'sec-ch-ua': '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36'
    }

    cookies = {
        'locale': 'en_PK',
        'cookie_version': '1.1',
        'optimizelySession': '0',
        'ssr_i18n': 'en',
        'user_i18n': 'en',
        '__Host-csrf': '6a9129bf-3c21-4f7c-9f9a-6e17d2ec4efb',

        'g_state': '{"i_l":0,"i_ll":1770238012060,"i_b":"3XbFDcHczeTuuEcP9ywPehQsg+szzBpyv+Pm+y4sHV8","i_e":{"enable_itp_optimization":15}}'
    }
    #
    # response = requests.get(url, headers=headers, cookies=cookies)
    #
    # print(f"Status Code: {response.status_code}")
    # print(f"Response: {response.text}")

    from curl_cffi import requests
    import json

    url = "https://www.jobleads.com/api/v2/search/v2/facets"

    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-US,en;q=0.9",
        # "authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9....",  # keep full token
        "content-type": "application/json",
        "origin": "https://www.jobleads.com",
        "referer": "https://www.jobleads.com/search/jobs?location_country=BHR&minSalary=14000&maxSalary=-1&filter_by_daysReleased=31&location_radius=50",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest",
    }

    cookies = {
        "locale": "en_PK",
        "cookie_version": "1.1",
        "jlst": "1f0ffaa5-4f50-6398-8660-0dd9927f615c",
        # "__Host-csrf": "6a9129bf-3c21-4f7c-9f9a-6e17d2ec4efb",
        # "prodsid": "2l92h60bplv3kca5pg4oq0eq2l",
    }

    payload = {
        "keywords": "",
        "location": "",
        "country": "BHR",
        "radius": 0,
        "minSalary": 14000,
        "maxSalary": -1,
        # "initialSearchId": 360585065,
        # "refinedSearchId": 66434204,
        "lastExecutedSearch": None,
        "searchFiltering": 0,
        "featuredJobs": "",
        "origin": 1,
        "savedSearchId": None,
        "startIndex": 0,
        "limit": 25,
        "filters": {
            "daysReleased": "31"
        }
    }

    response = requests.post(
        url,
        headers=headers,
        cookies=cookies,
        json=payload,
        impersonate="chrome123",  # 🔥 critical
        timeout=30
    )

    print(response.status_code)
    print(response.json())