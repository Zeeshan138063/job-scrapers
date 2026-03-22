import logging
import time
from typing import Optional, Dict

from curl_cffi import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_not_exception_type

from .exceptions import InvalidCredentialsError, AccountBlockedError, AuthServiceError
from .utils import jwt_payload

logger = logging.getLogger(__name__)


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

        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-US,en;q=0.9",
            "origin": "https://www.jobleads.com",
            "referer": "https://www.jobleads.com/",
            "user-agent": "Mozilla/5.0",
            "x-requested-with": "XMLHttpRequest",
            "content-type": f"multipart/form-data; boundary={boundary}",
        }

        r = self.s.post(url, headers=headers, data=body, impersonate=self.impersonate)
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

    def refresh_if_needed(self, skew_seconds: int = 120):
        if not self.token or time.time() >= (self.exp - skew_seconds):
            self.token = self.login_and_get_token()
            payload = jwt_payload(self.token)
            self.exp = int(payload.get("exp", 0))

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

        r = self.s.request(method, url, headers=hdrs, impersonate=self.impersonate, **kwargs)

        if r.status_code in (401, 403):
            if retry:
                logger.info(f"Auth failure ({r.status_code}) for {self.email}. Attempting token refresh...")
                self.token = None
                self.exp = 0
                try:
                    self.refresh_if_needed(0)
                except (InvalidCredentialsError, AccountBlockedError):
                    raise
                except Exception as e:
                    logger.error(f"Refresh failed during mid-crawl request: {e}")
                    raise AuthServiceError(f"Refresh failed: {e}")

                hdrs["authorization"] = f"Bearer {self.token}"
                r = self.s.request(method, url, headers=hdrs, impersonate=self.impersonate, **kwargs)

                if r.status_code in (401, 403):
                    logger.error(f"Permanent auth failure ({r.status_code}) for {self.email} after refresh.")
                    raise AccountBlockedError(f"Account rejected after refresh: {r.status_code}")
            else:
                logger.error(f"Auth failure ({r.status_code}) for {self.email} (Retries disabled).")
                raise AccountBlockedError(f"Auth failure without retry: {r.status_code}")

        return r

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_not_exception_type(InvalidCredentialsError),
        reraise=True
    )
    def get_job_details(self, job_id: str) -> dict:
        """Fetch details for a specific job ID (V1 or V3 fallback)."""
        # Try V1 first
        url_v1 = f"https://www.jobleads.com/api/v1/public/job/{job_id}"
        try:
            r = self.request("GET", url_v1)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            logger.warning(f"⚠️ V1 details failed for {job_id}: {e}. Retrying with V3...")

        # Fallback to V3
        url_v3 = f"https://www.jobleads.com/api/v3/job/detailsForAppNew/en_USA/{job_id}?language=en"
        r = self.request("GET", url_v3)
        r.raise_for_status()
        return r.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_not_exception_type(InvalidCredentialsError),
        reraise=True
    )
    def fetch_job_page_html(self, canonical_url: str) -> str:
        """Fetch public SSR HTML page for a job (no auth required)."""
        r = requests.get(canonical_url, headers={"user-agent": "Mozilla/5.0", "accept": "text/html"}, timeout=30)
        r.raise_for_status()
        return r.text

    def get_cookies_dict(self) -> Dict[str, str]:
        """Returns current session cookies as a flat dictionary."""
        return self.s.cookies.get_dict()
