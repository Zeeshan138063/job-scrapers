import json
import logging
import re
from typing import Dict, Any, Optional

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class JobExtractor:
    """
    Modular Job Extractor ported from original scraper.
    Uses JSON-LD, Nuxt Data, and DOM extraction.
    """

    def extract(self, html: str, hostname_hint: Optional[str] = None) -> Dict[str, Any]:
        """
        Main entry point.
        Returns structured job data.
        """
        if not html:
            return {}

        # Use lxml for speed/consistency as in original
        soup = BeautifulSoup(html, "lxml")

        # 1. Try JSON-LD first (most stable)
        json_ld = self._extract_json_ld(soup)

        # 2. Extraction of Source URL and Salary from Nuxt Data 
        # (Do this before DOM extraction destroys scripts)
        nuxt_data = self._extract_nuxt_data(soup, hostname_hint=hostname_hint)

        # 3. Fallback to DOM extraction
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
            # Raise or return empty - original raised ValueError but we can be more lenient in modular
            return {}

        # Merge nuxt_data (contains source_url, potentially salary)
        if nuxt_data:
            # Prioritize Nuxt salary if missing in JSON-LD/DOM
            if nuxt_data.get("salary") and not final_data.get("salary"):
                final_data["salary"] = nuxt_data["salary"]

            if nuxt_data.get("source_url"):
                final_data["source_url"] = nuxt_data["source_url"]

        return final_data

    def _extract_nuxt_data(self, soup: BeautifulSoup, hostname_hint: Optional[str] = None) -> Dict[str, Any]:
        """Extract original source URL and other details from Nuxt data."""
        script = soup.find("script", id="__NUXT_DATA__")
        if not script or not script.string:
            return {}

        result = {}
        # Extract URLs
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

        # Extract Salary
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

    def _extract_json_ld(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """Extract JobPosting from JSON-LD scripts."""
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
            except Exception:
                continue
        return None

    def _is_jobposting(self, data: Dict[str, Any]) -> bool:
        return isinstance(data, dict) and data.get("@type") == "JobPosting"

    def _normalize_json_ld(self, data: Dict[str, Any]) -> Dict[str, Any]:
        result = {
            "title": data.get("title"),
            "date_posted": data.get("datePosted"),
            "valid_through": data.get("validThrough"),
            "employment_type": data.get("employmentType"),
            "description_html": data.get("description"),
            "raw_json_ld": data
        }
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
            result["location"] = {
                "city": address.get("addressLocality"),
                "region": address.get("addressRegion"),
                "country": address.get("addressCountry")
            }
        return result

    def _extract_from_dom(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """Fallback DOM extraction."""
        # Clean soup copy safely
        temp_soup = BeautifulSoup(str(soup), "lxml")
        for tag in temp_soup.find_all(
                ["script", "style", "noscript", "header", "footer", "nav", "img", "picture", "svg", "video", "source",
                 "iframe", "form", "button"]):
            tag.decompose()

        job_card = temp_soup.find("div", {"data-testid": "job-preview-card"})
        if not job_card:
            return None

        result = {}
        h1 = job_card.find("h1")
        if h1: result["title"] = h1.get_text(strip=True)
        h2 = job_card.find("h2")
        if h2: result["company_name"] = h2.get_text(strip=True)
        salary_tag = job_card.find("div", {"data-testid": "job-card-chip-salary"})
        if salary_tag: result["salary_text"] = salary_tag.get_text(strip=True)

        desc_container = job_card.find("div", class_="new-job-preview-description-content")
        if desc_container:
            result["description_html"] = desc_container.decode_contents()
            result["description_text"] = desc_container.get_text("\n", strip=True)

        return result if result else None
