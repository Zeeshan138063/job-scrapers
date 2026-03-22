import base64
import json
import logging
from typing import Dict, Any, Generator

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def jwt_payload(token: str) -> dict:
    """Decode JWT payload (no signature verification, exp only)."""
    try:
        payload_b64 = token.split(".")[1]
        payload_b64 += "=" * (-len(payload_b64) % 4)
        return json.loads(base64.urlsafe_b64decode(payload_b64))
    except Exception:
        return {}


def iter_classic_search(client, payload: Dict[str, Any], headers: Dict[str, str],
                        page_size: int = 25) -> Generator[dict, None, None]:
    """Generator for JobLeads search pagination."""
    start = 0
    logger.info(f"🔍 Starting classic search iteration...")
    while True:
        payload["startIndex"] = start
        payload["limit"] = page_size

        try:
            r = client.request("POST", "https://www.jobleads.com/api/v2/search/v2", headers=headers, json=payload)
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


def remove_noise(soup: BeautifulSoup):
    """Remove common noise tags from JobLeads HTML."""
    for tag in soup(
            ["script", "style", "noscript", "header", "footer", "nav", "img", "picture", "svg", "video", "source",
             "iframe", "form", "button"]):
        tag.decompose()
