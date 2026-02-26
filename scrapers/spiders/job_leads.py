import os
import json
import re
import logging
import time
import base64
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Generator, List

import scrapy
from bs4 import BeautifulSoup
from curl_cffi import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, retry_if_not_exception_type

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scrapers.items import JobItem
from scrapers.utils.credential_manager import CredentialManager


class InvalidCredentialsError(Exception):
    """Raised when the login credentials are explicitly rejected by the server."""
    pass


class AccountBlockedError(Exception):
    """Raised when the account is blocked or suspended."""
    pass


class AuthServiceError(Exception):
    """Raised when the authentication service is unreachable or rate-limited."""
    pass


# -------------------------------------------------------------------
# Logging Configuration
# -------------------------------------------------------------------
logger = logging.getLogger(__name__)

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
# Client (Ported from job_leads_v1.py)
# -------------------------------------------------------------------

class JobleadsClient:
    """
    JobLeads client with:
    - login
    - split JWT handling (jwt_hp + jwt_s)
    - auto refresh
    - built-in retries
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
    @retry(
        stop=stop_after_attempt(3), 
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_not_exception_type(InvalidCredentialsError), 
        reraise=True
    )
    def login_and_get_token(self) -> str:
        logger.info(f"🔑 Attempting login for {self.email}...")
        url = "https://www.jobleads.com/user/login/form"

        boundary = "----WebKitFormBoundary6QwfUhHc0phBQ9U6"
        body = (f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="email"\r\n\r\n{self.email}\r\n'
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="password"\r\n\r\n{self.password}\r\n'
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="autoLogin"\r\n\r\n0\r\n'
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="redirectBackUrl"\r\n\r\n/home\r\n'
                f"--{boundary}--\r\n")

        headers = {"accept": "application/json, text/plain, */*", "accept-language": "en-US,en;q=0.9",
            "origin": "https://www.jobleads.com", "referer": "https://www.jobleads.com/", "user-agent": "Mozilla/5.0",
            "x-requested-with": "XMLHttpRequest", "content-type": f"multipart/form-data; boundary={boundary}", }

        r = self.s.post(url, headers=headers, data=body, impersonate=self.impersonate, )
        if r.status_code != 200:
            logger.error(f"❌ Login failed for {self.email} with status {r.status_code}: {r.text[:200]}")
            if r.status_code == 401:
                if "The entered login data is invalid." in r.text:
                    raise InvalidCredentialsError(f"Invalid credentials for {self.email}")
                elif "blocked" in r.text.lower() or "suspended" in r.text.lower():
                    raise AccountBlockedError(f"Account blocked for {self.email}")
            elif r.status_code in (429, 502, 503, 504):
                raise AuthServiceError(f"Temporary auth service failure ({r.status_code})")
        r.raise_for_status()

        hp = self.s.cookies.get("jwt_hp")
        sig = self.s.cookies.get("jwt_s")

        if not hp or not sig:
            raise RuntimeError("Login OK but jwt_hp/jwt_s missing")

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
    @retry(
        stop=stop_after_attempt(3), 
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_not_exception_type(InvalidCredentialsError), 
        reraise=True
    )
    def request(self, method: str, url: str, *, headers=None, retry=True, **kwargs):
        self.refresh_if_needed()

        hdrs = dict(headers or {})
        hdrs["authorization"] = f"Bearer {self.token}"

        r = self.s.request(method, url, headers=hdrs, impersonate=self.impersonate, **kwargs, )

        if retry and r.status_code in (401, 403):
            self.token = None
            self.exp = 0
            self.refresh_if_needed(0)
            hdrs["authorization"] = f"Bearer {self.token}"

            r = self.s.request(method, url, headers=hdrs, impersonate=self.impersonate, **kwargs, )

        return r

    @retry(
        stop=stop_after_attempt(3), 
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_not_exception_type(InvalidCredentialsError), 
        reraise=True
    )
    def get_job_details(self, job_id: str) -> dict:
        """
        Fetch details for a specific job ID.
        Attempts V1 API first. If that fails, falls back to V3 API.
        """
        # time.sleep(1)

        # Try V1 first
        url_v1 = f"https://www.jobleads.com/api/v1/public/job/{job_id}"
        try:
            r = self.request("GET", url_v1)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            logger.warning(f"⚠️ V1 details failed for {job_id}: {e}. Retrying with V3...")
        
        # time.sleep(2)
        # Fallback to V3
        url_v3 = f"https://www.jobleads.com/api/v3/job/detailsForAppNew/en_USA/{job_id}?language=en"
        r = self.request("GET", url_v3)
        r.raise_for_status()
        return r.json()

    # ---------------------------------
    # Fetch Canonical Job HTML Page
    # ---------------------------------
    @retry(
        stop=stop_after_attempt(3), 
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_not_exception_type(InvalidCredentialsError), 
        reraise=True
    )
    def fetch_job_page_html(self, canonical_url: str) -> str:
        """
        Fetch public SSR HTML page for a job.
        No auth required.
        """

        r = requests.get(canonical_url, headers={"user-agent": "Mozilla/5.0", "accept": "text/html", }, timeout=30, )
        r.raise_for_status()
        return r.text

    def extract_job_details_after_noise_removal(self, job_card):
        data = {}

        data["title"] = job_card.find("h1").get_text(strip=True)

        company = job_card.find("h2")
        data["company"] = company.get_text(strip=True) if company else None

        salary = job_card.find("div", {"data-testid": "job-card-chip-salary"})
        data["salary"] = salary.get_text(strip=True) if salary else None

        summary = job_card.find("div", {"data-testid": "job-card-summary"})
        data["summary"] = summary.get_text(" ", strip=True) if summary else None

        full_desc = job_card.find("div", class_="new-job-preview-description-content")
        data["description_html"] = full_desc.get_text("\n", strip=True) if full_desc else None

        return data

    def extract_jobposting_jsonld(self, html_text: str) -> dict:
        soup = BeautifulSoup(html_text, "lxml")
        # remove the noise
        for tag in soup(
                ["script", "style", "noscript", "header", "footer", "nav", "img", "picture", "svg", "video", "source"]):
            tag.decompose()

        job_card = soup.find("div", {"data-testid": "job-preview-card"})
        if job_card:
            return self.extract_job_details_after_noise_removal(job_card)

        # 1. Try standard ID
        script = soup.find("script", {"type": "application/ld+json", "id": "jobPostingLdjson"})

        # 2. Fallback: Search all ld+json for @type="JobPosting"
        if not script or not script.string:
            scripts = soup.find_all("script", {"type": "application/ld+json"})
            for s in scripts:
                if s.string:
                    try:
                        data = json.loads(s.string.strip())
                        if data.get("@type") == "JobPosting":
                            return self.normalize_jobposting(data)
                    except:
                        continue
            raise ValueError("JobPosting JSON-LD not found in HTML")

        return json.loads(script.string.strip())

    def normalize_jobposting(self, data: dict) -> dict:
        # description is HTML (escaped inside JSON)
        desc_html = data.get("description")

        return {"job_id": (data.get("identifier") or {}).get("value"), "title": data.get("title"),
            "company": (data.get("hiringOrganization") or {}).get("name"),
            "employment_type": data.get("employmentType"), "date_posted": data.get("datePosted"),
            "valid_through": data.get("validThrough"),
            "location": {"city": (((data.get("jobLocation") or {}).get("address") or {}).get("addressLocality")),
                "region": (((data.get("jobLocation") or {}).get("address") or {}).get("addressRegion")),
                "country": (((data.get("jobLocation") or {}).get("address") or {}).get("addressCountry")), },
            "salary": {"currency": data.get("salaryCurrency"),
                "min": (((data.get("baseSalary") or {}).get("value") or {}).get("minValue")),
                "max": (((data.get("baseSalary") or {}).get("value") or {}).get("maxValue")),
                "unit": (((data.get("baseSalary") or {}).get("value") or {}).get("unitText")), },
            "description_html": desc_html, }


# -------------------------------------------------------------------
# Job Extractor (Ported from job_leads_v1.py)
# -------------------------------------------------------------------

class JobExtractor:

    def extract(self, html: str, hostname_hint: Optional[str] = None) -> Dict[str, Any]:
        """
        Main entry point.
        Returns structured job data.
        Raises ValueError if nothing found.
        """

        soup = BeautifulSoup(html, "lxml")

        # 1️⃣ Try JSON-LD first (most stable)
        json_ld = self._extract_json_ld(soup)

        # 2️⃣ Extraction of Source URL and Salary from Nuxt Data (Do this before DOM extraction destroys scripts)
        nuxt_data = self._extract_nuxt_data(soup, hostname_hint=hostname_hint)

        # 3️⃣ Fallback to DOM extraction
        dom_data = self._extract_from_dom(soup)

        # Merge results
        final_data = {}
        if json_ld:
            final_data = json_ld
        elif dom_data:
            final_data = dom_data
            
        # Ensure company_name is mapped from company if we found it in DOM/LD
        if "company" in final_data and "company_name" not in final_data:
            final_data["company_name"] = final_data.pop("company")
        elif not final_data and not nuxt_data:
            raise ValueError("JobPosting not found in HTML")
                
        # Merge nuxt_data (contains source_url, potentially salary)
        if nuxt_data:
            # Prioritize Nuxt salary if missing in JSON-LD/DOM
            if nuxt_data.get("salary") and not final_data.get("salary"):
                final_data["salary"] = nuxt_data["salary"]
            
            if nuxt_data.get("source_url"):
                final_data["source_url"] = nuxt_data["source_url"]

        return final_data

    # ---------------------------------------------------

    def _extract_nuxt_data(self, soup: BeautifulSoup, hostname_hint: Optional[str] = None) -> Dict[str, Any]:
        """
        Extract the original source URL and other details from Nuxt application data.
        Uses a priority-based heuristic to find the source URL.
        """
        script = soup.find("script", id="__NUXT_DATA__")
        if not script or not script.string:
            return {}

        result = {}
        
        # 1. Extract Source URL
        urls = re.findall(r'https?://[^\s",<>\\\]]+', script.string)
        
        noise_domains = [
            "jobleads.com", "googletagmanager.com", "google-analytics.com", 
            "facebook.net", "facebook.com", "optimizely.com", "hotjar.com",
            "cloudfront.net", "akamaihd.net", "w3.org", "schema.org",
            "doubleclick.net", "bing.com", "adnxs.com"
        ]
        
        job_boards = [
            "linkedin.com", "indeed.com", "glassdoor.com", "ziprecruiter.com",
            "monster.com", "careerbuilder.com", "simplyhired.com", "dice.com",
            "stepstone", "personio", "lever.co", "greenhouse.io", "workable.com",
            "smartrecruiters.com", "bamboohr.com", "xing.com", "talents.com"
        ]

        job_patterns = ["/jobs/", "/job/", "/view/", "/vacancy/", "/career/", "/recruitment/", "/apply/"]

        candidates = []
        for url in urls:
            if any(domain in url for domain in noise_domains):
                continue
            
            if hostname_hint and hostname_hint in url:
                candidates.append((1, url))
                continue

            if any(board in url for board in job_boards):
                candidates.append((2, url))
                continue

            if any(pattern in url.lower() for pattern in job_patterns):
                candidates.append((3, url))
                continue
            
            candidates.append((4, url))

        if candidates:
            candidates.sort(key=lambda x: (x[0], -len(x[1])))
            result["source_url"] = candidates[0][1]

        # 2. Extract Salary
        salary_min_match = re.search(r'"salaryMin":\s*(\d+)', script.string)
        salary_max_match = re.search(r'"salaryMax":\s*(\d+)', script.string)
        currency_match = re.search(r'"currency":\s*"([^"]+)"', script.string)
        
        if salary_min_match or salary_max_match:
            result["salary"] = {
                "min": int(salary_min_match.group(1)) if salary_min_match else None,
                "max": int(salary_max_match.group(1)) if salary_max_match else None,
                "currency": currency_match.group(1) if currency_match else None
            }

        return result

    # ---------------------------------------------------

    def _extract_json_ld(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """
        Extract JobPosting from JSON-LD scripts.
        """
        scripts = soup.find_all("script", {"type": "application/ld+json"})

        for script in scripts:
            if not script.string:
                continue

            try:
                data = json.loads(script.string.strip())
                if isinstance(data, list):
                    for item in data:
                        if self._is_jobposting(item):
                            return self._normalize_json_ld(item)

                if isinstance(data, dict):
                    if self._is_jobposting(data):
                        return self._normalize_json_ld(data)

            except json.JSONDecodeError:
                continue

        return None

    def _is_jobposting(self, data: Dict[str, Any]) -> bool:
        return isinstance(data, dict) and data.get("@type") == "JobPosting"

    def _normalize_json_ld(self, data: Dict[str, Any]) -> Dict[str, Any]:
        result = {"title": data.get("title"), "date_posted": data.get("datePosted"),
            "valid_through": data.get("validThrough"), "employment_type": data.get("employmentType"),
            "description_html": data.get("description"), "raw_json_ld": data}

        org = data.get("hiringOrganization")
        if isinstance(org, dict):
            result["company_name"] = org.get("name")

        base_salary = data.get("baseSalary")
        if isinstance(base_salary, dict):
            value = base_salary.get("value", {})
            result["salary"] = {
                "min": value.get("minValue"),
                "max": value.get("maxValue"),
                "currency": base_salary.get("currency"),
                "unit": value.get("unitText")
            }

        location = data.get("jobLocation")
        if isinstance(location, dict):
            address = location.get("address", {})
            result["location"] = {"city": address.get("addressLocality"), "region": address.get("addressRegion"),
                "country": address.get("addressCountry")}

        return result

    def _extract_from_dom(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        for tag in soup.find_all(
                ["script", "style", "noscript", "header", "footer", "nav", "img", "picture", "svg", "video", "source",
                    "iframe", "form", "button"]):
            tag.decompose()

        job_card = soup.find("div", {"data-testid": "job-preview-card"})
        if not job_card:
            return None

        result = {}
        h1 = job_card.find("h1")
        if h1:
            result["title"] = h1.get_text(strip=True)
        h2 = job_card.find("h2")
        if h2:
            result["company_name"] = h2.get_text(strip=True)
        salary_tag = job_card.find("div", {"data-testid": "job-card-chip-salary"})
        if salary_tag:
            result["salary_text"] = salary_tag.get_text(strip=True)

        desc_container = job_card.find("div", class_="new-job-preview-description-content")
        if desc_container:
            result["description_html"] = desc_container.decode_contents()
            result["description_text"] = desc_container.get_text("\n", strip=True)

        return result if result else None


# -------------------------------------------------------------------
# Classic Search (pagination)
# -------------------------------------------------------------------

def iter_classic_search(client: JobleadsClient, payload: Dict[str, Any], headers: Dict[str, str],
        page_size: int = 25, ) -> Generator[dict, None, None]:
    start = 0
    logger.info(f"🔍 Starting classic search iteration...")
    while True:
        payload["startIndex"] = start
        payload["limit"] = page_size

        try:
            r = client.request("POST", "https://www.jobleads.com/api/v2/search/v2", headers=headers, json=payload, )
            r.raise_for_status()
            data = r.json()

            jobs = data.get("jobs") or data.get("resultList") or []
            if not jobs:
                break
            for job in jobs:
                yield job
            if len(jobs) < page_size:
                break
            start += len(jobs)
        except Exception as e:
            logger.error(f"❌ Failed to fetch page {start} after retries: {e}. Stopping pagination.")
            break


# -------------------------------------------------------------------
# Data Mapping
# -------------------------------------------------------------------

def map_listing_response(job_data: dict) -> dict:
    meta = {"is_featured": job_data.get("isFeatured"), "is_promoted": job_data.get("isPromoted"),
        "is_deactivated": job_data.get("isDeactivated"), "source_type": job_data.get("source"),
        "contract_type_raw": job_data.get("contractType"),
    }

    ctype = job_data.get("contractType")
    employment_type = None
    if isinstance(ctype, list) and len(ctype) > 0:
        employment_type = ctype[0]
    elif isinstance(ctype, str):
        employment_type = ctype
    
    location_raw = job_data.get("location")
    location_parsed = {}
    if location_raw and isinstance(location_raw, str):
        parts = location_raw.split(",")
        if len(parts) > 0:
            location_parsed["city"] = parts[0].strip()
        if len(parts) > 1:
            location_parsed["country"] = parts[-1].strip()

    res = {
        "source": "jobleads",
        "external_id": job_data.get("id"), 
        "source_domain": "jobleads.com", 
        "scraped_source": "job_leads_spider",
        "title": job_data.get("title"), 
        "company": "JobLeads (Aggregator)", 
        "company_name": "JobLeads (Aggregator)", 
        "location": location_raw,
        "location_parsed": location_parsed,
        "url": f"https://www.jobleads.com/job/{job_data.get('id')}", 
        "salary_raw": str(job_data.get("salary")) if job_data.get("salary") else None, 
        "employment_type": employment_type,
        "remote_modality": job_data.get("isRemote"),
        "meta_flags": meta,
        "_raw_listing": job_data
    }
    return res


def map_details_response(api_response: dict) -> dict:
    if not api_response:
        return {}
    content = api_response.get("payload", {}).get("content", {})
    url_slug = content.get("canonicalUrl", "")
    full_url = f"https://www.jobleads.com/{url_slug.lstrip('/')}" if url_slug else None
    company = content.get("hiringOrganization", {}).get("name")

    res = {
        "salary_currency": content.get("currency"), 
        "salary_min": content.get("salaryMin"),
        "salary_max": content.get("salaryMax"), 
        "region": content.get("locationRegion"),
        "hostname_origin": content.get("hostname"), 
        "url": full_url, 
        "description_short": content.get("jobSummary"),
        "benefits": content.get("benefits"), 
        "qualifications": content.get("qualifications"),
        "responsibilities": content.get("responsibilities"), 
        "skills": content.get("skills"),
        "education": content.get("education"), 
        "tools": content.get("tools"),
        "meta_flags": {
            "is_accessible": content.get("isAccessible"),
            "is_deactivated": content.get("isDeactivated"),
            "posted_since": content.get("releasedSince"),
        },
        "posted_at": content.get("postedAt"), 
        "expires_at": content.get("validThrough"),
        "_raw_details": content
    }
    if company:
        res["company"] = company
        res["company_name"] = company
    return res

def map_canonical_response(normalized_data: dict) -> dict:
    if not normalized_data:
        return {}
    salary = normalized_data.get("salary") or {}
    location_data = normalized_data.get("location") or {}
    location_parsed = {}
    if isinstance(location_data, dict):
        location_parsed["city"] = location_data.get("city")
        location_parsed["country"] = location_data.get("country")
        location_parsed["state"] = location_data.get("region")
    res = {
        "salary_currency": normalized_data.get("salaryCurrency") or (normalized_data.get("salary") or {}).get("currency"),
        "salary_min": (normalized_data.get("salary") or {}).get("min"),
        "salary_max": (normalized_data.get("salary") or {}).get("max"),
        "description": normalized_data.get("description_html"),
        "description_html": normalized_data.get("description_html"),
        "description_text": normalized_data.get("description_text"),
        "salary_period": salary.get("unit"),
        "country_code": location_data.get("country"),
        "location_parsed": location_parsed,
        "source_url": normalized_data.get("source_url"),
        "_raw_canonical": normalized_data
    }
    company = normalized_data.get("company_name") or normalized_data.get("company")
    if company:
        res["company"] = company
        res["company_name"] = company
    return res


# -------------------------------------------------------------------
# Scrapy Spider
# -------------------------------------------------------------------

class JobLeadsSpider(scrapy.Spider):
    name = "jobleads"
    allowed_domains = ["jobleads.com"]
    custom_settings = {
        'ROBOTSTXT_OBEY': False,
        'CONCURRENT_REQUESTS': 4,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 2,
        'DOWNLOAD_DELAY': 3,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 5,
        'AUTOTHROTTLE_MAX_DELAY': 60,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 1.0,
        'AUTOTHROTTLE_DEBUG': True,
    }

    def __init__(self, country=None, limit=None, *args, **kwargs):
        super(JobLeadsSpider, self).__init__(*args, **kwargs)
        self.country_arg = country.upper() if country else None
        self.limit = int(limit) if limit else None
        
        creds_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../config/jobleads_creds.json"))
        self.cm = CredentialManager(creds_file)
        self.configs = self.cm.get_configs_for_startup(self.country_arg)

    def _mark_credentials_invalid(self, country_code: str, email: str, reason: str = "blocked"):
        self.cm.mark_blocked(country_code, email, reason)

    def start_requests(self):
        if not self.configs:
            self.logger.error("No configurations loaded. Check jobleads_creds.json")
            return

        for config in self.configs:
            country = config['country_code']
            country_name = config.get('country_name')
            email = config.get('email')
            password = config.get('password')
            
            if not email or not password:
                self.logger.warning(f"Missing credentials for {country}")
                continue

            self.logger.info(f"🚀 Starting scraper for country: {country} using {email}")
            try:
                client = JobleadsClient(email=email, password=password)
                # We don't yield the Request yet because we want to catch login errors synchronously if possible
                # or just handle them in the callback. For robustness, let's catch start-up login errors.
                client.refresh_if_needed() 
                
                yield scrapy.Request(
                    url="https://www.jobleads.com", 
                    callback=self.parse_country, 
                    cb_kwargs={'client': client, 'country': country, 'country_name': country_name},
                    dont_filter=True
                )
            except InvalidCredentialsError:
                self.logger.error(f"❌ Invalid credentials for {country} ({email}). Marking as blocked.")
                self._mark_credentials_invalid(country, email, "invalid_credentials")
            except AccountBlockedError:
                self.logger.error(f"❌ Account BLOCKED for {country} ({email}). Marking as blocked.")
                self._mark_credentials_invalid(country, email, "blocked")
            except Exception as e:
                self.logger.error(f"Failed to initialize client for {country}: {e}")

    def parse_country(self, response, client, country, country_name):
        self.logger.info(f"📍 Parsing country: {country} ({country_name})")
        try:
            client.refresh_if_needed()
        except (InvalidCredentialsError, AccountBlockedError):
            self.logger.error(f"❌ Auth failed for {country} ({client.email}) in parse_country. Marking blocked.")
            self._mark_credentials_invalid(country, client.email, "mid_crawl_auth_failure")
            return
        
        payload = {
            "country": country, 
            "maxSalary": -1, 
            "startIndex": 0, 
            "limit": self.limit or 25, 
            "filters": {"daysReleased": "1"}
        }
        headers = {
            "accept": "application/json", 
            "content-type": "application/json", 
            "user-agent": "Mozilla/5.0",
            "authorization": f"Bearer {client.token}"
        }

        yield scrapy.Request(
            url="https://www.jobleads.com/api/v2/search/v2",
            method="POST",
            body=json.dumps(payload),
            headers=headers,
            callback=self.parse_search_results,
            cb_kwargs={'client': client, 'country': country, 'country_name': country_name, 'headers': headers, 'payload': payload, 'count': 0},
            meta={'use_curl_cffi': True},
            dont_filter=True
        )

    def parse_search_results(self, response, client, country, country_name, headers, payload, count):
        try:
            data = json.loads(response.text)
            jobs = data.get("jobs") or data.get("resultList") or []
            
            if not jobs:
                self.logger.info(f"🏁 No more jobs found for {country}")
                return

            for job_listing in jobs:
                if self.limit and count >= self.limit:
                    return
                
                job_id = job_listing.get("id")
                if not job_id:
                    continue
                
                mapped_listing = map_listing_response(job_listing)
                
                # Fetch details asynchronously
                # Try V1 first
                url_v1 = f"https://www.jobleads.com/api/v1/public/job/{job_id}"
                yield scrapy.Request(
                    url=url_v1,
                    callback=self.parse_job_details,
                    cb_kwargs={
                        'client': client, 
                        'country': country,
                        'country_name': country_name,
                        'job_id': job_id, 
                        'mapped_listing': mapped_listing
                    },
                    meta={
                        'use_curl_cffi': True,
                        'handle_httpstatus_list': [404]
                    },
                    dont_filter=True
                )
                count += 1

            # Pagination
            if len(jobs) >= (payload.get('limit') or 25) and (not self.limit or count < self.limit):
                new_payload = payload.copy()
                new_payload["startIndex"] = payload["startIndex"] + len(jobs)
                
                yield scrapy.Request(
                    url="https://www.jobleads.com/api/v2/search/v2",
                    method="POST",
                    body=json.dumps(new_payload),
                    headers=headers,
                    callback=self.parse_search_results,
                    cb_kwargs={'client': client, 'country': country, 'country_name': country_name, 'headers': headers, 'payload': new_payload, 'count': count},
                    meta={'use_curl_cffi': True},
                    dont_filter=True
                )
        except (InvalidCredentialsError, AccountBlockedError):
            self.logger.error(f"❌ Auth failed for {country} ({client.email}) in parse_search_results. Marking blocked.")
            self._mark_credentials_invalid(country, client.email, "mid_crawl_auth_failure")
        except Exception as e:
            self.logger.error(f"Error parsing search results for {country}: {e}")

    def parse_job_details(self, response, client, country, country_name, job_id, mapped_listing):
        mapped_details = {}
        details_resp = None
        
        if response.status in (401, 403):
            self.logger.error(f"❌ Auth failed (HTTP {response.status}) for {job_id} using {client.email}. Marking blocked.")
            self._mark_credentials_invalid(country, client.email, "http_auth_failure")
            return
        
        if response.status == 200:
            try:
                details_resp = json.loads(response.text)
                mapped_details = map_details_response(details_resp)
            except Exception as e:
                self.logger.warning(f"Error parsing V1 details for {job_id}: {e}")
        
        if not mapped_details:
            # Fallback to V3
            # In a real async refactor, we would yield another Request here
            # But to keep it simple and avoid callback hell for now, 
            # we check if we already tried V3.
            if "api/v1" in response.url:
                url_v3 = f"https://www.jobleads.com/api/v3/job/detailsForAppNew/en_USA/{job_id}?language=en"
                self.logger.info(f"⚠️ V1 failed for {job_id}, retrying with V3...")
                yield scrapy.Request(
                    url=url_v3,
                    callback=self.parse_job_details,
                    cb_kwargs={
                        'client': client, 
                        'country': country,
                        'country_name': country_name,
                        'job_id': job_id, 
                        'mapped_listing': mapped_listing
                    },
                    meta={
                        'use_curl_cffi': True,
                        'handle_httpstatus_list': [404]
                    },
                    dont_filter=True
                )
                return
            else:
                self.logger.warning(f"Both V1 and V3 failed for {job_id}")

        # Continue with Canonical & Source URL if we have details
        if details_resp:
            canonical_sub = details_resp.get('payload', {}).get('content', {}).get('canonicalUrl', "")
            if canonical_sub:
                _url = f"https://www.jobleads.com/{canonical_sub.lstrip('/')}"
                yield scrapy.Request(
                    url=_url,
                    callback=self.parse_canonical_page,
                    cb_kwargs={
                        'job_id': job_id,
                        'country_name': country_name,
                        'mapped_listing': mapped_listing,
                        'mapped_details': mapped_details
                    },
                    meta={'use_curl_cffi': True},
                    dont_filter=True
                )
                return

        # If no canonical URL, just yield what we have
        yield from self._yield_final_item(mapped_listing, mapped_details, {}, country_name)

    def parse_canonical_page(self, response, job_id, country_name, mapped_listing, mapped_details):
        mapped_canonical = {}
        try:
            extractor = JobExtractor()
            job_data = extractor.extract(response.text, hostname_hint=mapped_details.get("hostname_origin"))
            mapped_canonical = map_canonical_response(job_data)
        except Exception as e:
            self.logger.debug(f"Canonical extraction failed for {job_id}: {e}")
                    
        yield from self._yield_final_item(mapped_listing, mapped_details, mapped_canonical, country_name)

    def _yield_final_item(self, listing, details, canonical, country_name=None):
        # Merge
        item_dict = {**listing, **details, **canonical}
        
        # Unified company name
        final_company = item_dict.get('company_name') or item_dict.get('company')
        item_dict['company_name'] = final_company
        item_dict['company'] = final_company
        
        if canonical.get('location_parsed'):
             item_dict['location_parsed'] = canonical.get('location_parsed')

        # Additional fields for JobItem compatibility
        item_dict['scraped_at'] = datetime.now(timezone.utc).isoformat()
        item_dict['scraped_source'] = "job_leads_spider"
        item_dict['source'] = "jobleads"
        
        # Calculate dedup_hash early for better pipeline compatibility
        import hashlib
        dedup_src = f"jobleads:{item_dict.get('external_id')}"
        item_dict['dedup_hash'] = hashlib.md5(dedup_src.encode()).hexdigest()
        
        item_dict['raw_data'] = {
             "listing": item_dict.pop("_raw_listing", {}),
             "details": item_dict.pop("_raw_details", {}),
             "canonical": item_dict.pop("_raw_canonical", {})
        }
        
        if 'description' not in item_dict and 'description_html' in item_dict:
            item_dict['description'] = item_dict['description_html']

        item_dict['country_name'] = country_name
        yield JobItem(**item_dict)
#
if __name__ == "__main__":
    process = CrawlerProcess(get_project_settings())
    process.crawl(JobLeadsSpider, country="USA")
    process.start()
