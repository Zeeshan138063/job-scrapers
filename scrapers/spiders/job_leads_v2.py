import json
import scrapy
from scrapy.http import Request
from bs4 import BeautifulSoup
import logging
from scrapers.utils.config_loader import ConfigLoader

logger = logging.getLogger(__name__)

class JobLeadsSpiderV2(scrapy.Spider):
    name = "job_leads_v2"
    allowed_domains = ["jobleads.com"]
    start_urls = ["https://www.jobleads.com/"]

    def __init__(self, email=None, password=None, search_queries=None, locations=None, min_salary=40000, radius=0, filters=None, *args, **kwargs):
        super(JobLeadsSpiderV2, self).__init__(*args, **kwargs)
        self.email = email or "berapec475@ixunbo.com"
        self.password = password or "Berapec475@ixunbo.com"
        
        # Handle search_queries and locations from dashboard/worker
        if isinstance(search_queries, str):
            try:
                self.search_queries = json.loads(search_queries)
            except:
                self.search_queries = [q.strip() for q in search_queries.split(',')]
        else:
            self.search_queries = search_queries or ["python"]

        if isinstance(locations, str):
            try:
                self.locations = json.loads(locations)
            except:
                self.locations = [l.strip() for l in locations.split(',')]
        else:
            self.locations = locations or ["NLD"]

        # Filter out placeholders like "string" or empty strings
        self.locations = [l for l in self.locations if l and l.lower() not in ["string", "none", "null"]]
        if not self.locations:
            self.locations = [""]

        # Handle filters (can be JSON string or dict)
        self.filters = filters or {}
        if isinstance(self.filters, str):
            try:
                self.filters = json.loads(self.filters)
            except:
                self.filters = {}
            
        self.min_salary = int(min_salary)
        self.radius = int(radius)
        self.token = None
        
        # Initialize Config Loader
        self.config_loader = ConfigLoader()
        self.spider_config = self.config_loader.get_spider_config("jobleads")
        
        # Meta for curl_cffi middleware
        self.curl_meta = {
            "use_curl_cffi": True,
        }

    def start_requests(self):
        # 1) Session bootstrap
        logger.info("Step 1: Session bootstrap")
        yield Request(
            url="https://www.jobleads.com/",
            callback=self.login,
            meta=self.curl_meta,
            dont_filter=True
        )

    def login(self, response):
        # 2) Login -> produce Bearer token
        logger.info("Step 2: Login")
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
            "x-requested-with": "XMLHttpRequest",
            "referer": "https://www.jobleads.com/",
            "content-type": f"multipart/form-data; boundary={boundary}",
        }
        
        yield Request(
            url=url,
            method="POST",
            body=body,
            headers=headers,
            callback=self.after_login,
            meta=self.curl_meta,
            dont_filter=True
        )

    def after_login(self, response):
        # Extract JWT from cookies
        logger.info(f"Login Response Status: {response.status}")
        
        # Parse all cookies from Set-Cookie headers
        all_cookies = response.headers.getlist('Set-Cookie')
        cookie_dict = {}
        for c in all_cookies:
            try:
                decoded = c.decode('utf-8')
                name_val = decoded.split(';')[0]
                if '=' in name_val:
                    name, val = name_val.split('=', 1)
                    cookie_dict[name.strip()] = val.strip()
            except Exception as e:
                logger.error(f"Error parsing cookie header {c}: {e}")

        jwt_hp = cookie_dict.get('jwt_hp')
        jwt_s = cookie_dict.get('jwt_s')
        
        if not jwt_hp or not jwt_s:
            logger.error(f"Failed to find jwt_hp or jwt_s in cookies. Found: {list(cookie_dict.keys())}")
            return

        self.token = f"{jwt_hp}.{jwt_s}"
        logger.info("Successfully constructed Bearer token")

        # 4) Job discovery
        logger.info("Step 4: Job discovery (Classic Search)")
        for query in self.search_queries:
            for country in self.locations:
                logger.info(f"Searching for '{query}' in {country}")
                yield from self.fetch_search_page(0, query, country)

    def fetch_search_page(self, start_index, query, country_input, initial_search_id=0, refined_search_id=0):
        url = "https://www.jobleads.com/api/v2/search/v2"
        
        # Support "City,Country" format (e.g., "Lahore,PAK")
        city = ""
        country = country_input
        if ',' in country_input:
            parts = [p.strip() for p in country_input.split(',')]
            if len(parts) >= 2:
                city = parts[0]
                country = parts[1]
        
        # Determine if we have a valid country
        has_country = country and country.lower() not in ["", "string", "none", "null"]
        clean_country = country if has_country else ""
        
        # Start with standard fields
        payload = {
            "keywords": query,
            "location": city,
            "country": clean_country,
            "radius": self.radius,
            "minSalary": self.min_salary,
            "maxSalary": -1,
            "initialSearchId": initial_search_id,
            "refinedSearchId": refined_search_id,
            "lastExecutedSearch": None,
            "searchFiltering": 0,
            "featuredJobs": "",
            "origin": 1,
            "savedSearchId": None,
            "startIndex": start_index,
            "limit": 25,
            "filters": {},
        }
        
        # Dynamically inject filters from self.filters based on DB definitions
        registered_filters = self.spider_config.get("filters", {})
        for key, value in self.filters.items():
            filter_def = registered_filters.get(key)
            if filter_def:
                # Validation (Optional: can be more strict if needed)
                if filter_def["type"] == "select":
                    valid_values = [opt["value"] for opt in filter_def["options"]]
                    if value not in valid_values:
                        logger.warning(f"Invalid value '{value}' for filter '{key}'. Expected one of: {valid_values}")
                        # Skip or use default? For now, we'll keep it as is but warn.
                
                if filter_def["is_nested"]:
                    payload["filters"][key] = value
                else:
                    payload[key] = value
            else:
                # If not in DB, fallback to generic 'filters' nesting as per Jobleads convention
                payload["filters"][key] = value
        
        # Headers matched exactly to working classic_headers in job_leads.py
        referer_url = f"https://www.jobleads.com/search/jobs?keywords={query}"
        if city:
            referer_url += f"&location={city}"
        if has_country:
            referer_url += f"&location_country={clean_country}"
            
        headers = {
            "accept": "application/json, text/plain, */*",
            "content-type": "application/json",
            "authorization": f"Bearer {self.token}",
            "x-requested-with": "XMLHttpRequest",
            "origin": "https://www.jobleads.com",
            "referer": referer_url,
            "user-agent": "Mozilla/5.0",
        }
        
        yield Request(
            url=url,
            method="POST",
            body=json.dumps(payload),
            headers=headers,
            callback=self.parse_search_results,
            meta={
                **self.curl_meta, 
                "start_index": start_index,
                "query": query,
                "country": clean_country,
                "country_input": country_input,
                "city": city,
                "initial_search_id": initial_search_id,
                "refined_search_id": refined_search_id
            },
            dont_filter=True
        )

    def parse_search_results(self, response):
        data = json.loads(response.body)
        jobs = data.get("jobs", []) or data.get("resultList", [])
        
        # Extract dynamic IDs for intelligent pagination
        new_initial_id = data.get("initialSearchId", response.meta.get("initial_search_id", 0))
        new_refined_id = data.get("refinedSearchId", response.meta.get("refined_search_id", 0))

        query = response.meta['query']
        country = response.meta['country']
        
        logger.info(f"Found {len(jobs)} jobs for '{query}' in {country} on page starting at {response.meta['start_index']}")
        logger.debug(f"Search IDs in response: initial={new_initial_id}, refined={new_refined_id}")

        for job in jobs:
            job_id = job.get("id") or job.get("jobId")
            if job_id:
                # 5) Job details enrichment
                yield self.fetch_job_details(job_id)

        # Pagination
        if len(jobs) == 25:
            new_start = response.meta['start_index'] + 25
            yield from self.fetch_search_page(
                new_start, 
                query, 
                response.meta.get("country_input", country),
                initial_search_id=new_initial_id,
                refined_search_id=new_refined_id
            )

    def fetch_job_details(self, job_id):
        # Locale can be passed via spider args or determined from country, 
        # but the user said "no need to make default", so we'll use a placeholder or arg.
        locale = getattr(self, 'locale', 'en_US') 
        url = f"https://www.jobleads.com/api/v3/job/detailsForAppNew/{locale}/{job_id}?language=en"
        
        headers = {
            "authorization": f"Bearer {self.token}",
            "x-requested-with": "XMLHttpRequest",
            "referer": "https://www.jobleads.com/search/jobs",
        }
        
        return Request(
            url=url,
            headers=headers,
            callback=self.parse_job_details,
            meta={**self.curl_meta, "job_id": job_id},
            dont_filter=True
        )

    def parse_job_details(self, response):
        try:
            if response.status != 200:
                logger.error(f"Failed to fetch job details for {response.url}, status: {response.status}")
                return

            details = json.loads(response.body)
            payload = details.get('payload', {})
            content = payload.get('content', {})
            
            if not content:
                logger.error(f"No content found in job details for {response.url}")
                return

            canonical_url = content.get('canonicalUrl')
            job_id = response.meta.get('job_id')

            # Ensure minimal fields for ValidationPipeline
            content['source'] = 'jobleads'
            content['external_id'] = job_id
            
            if canonical_url:
                if not canonical_url.startswith('http'):
                    canonical_url = f"https://www.jobleads.com{canonical_url}"
                
                content['url'] = canonical_url
                
                # 5) Job page HTML (for JSON-LD)
                yield Request(
                    url=canonical_url,
                    callback=self.parse_job_page,
                    headers={"referer": response.url},
                    meta={**self.curl_meta, "job_details": content},
                    dont_filter=True
                )
            else:
                content['url'] = response.url
                yield content
        except Exception as e:
            logger.error(f"Error parsing job details for {response.url}: {e}")
            logger.debug(f"Response Body: {response.body.decode('utf-8', 'ignore')[:500]}")

    def parse_job_page(self, response):
        # Extract JSON-LD
        job_item = response.meta['job_details']
        
        try:
            soup = BeautifulSoup(response.body, "lxml")
            script = soup.find("script", {"type": "application/ld+json", "id": "jobPostingLdjson"})
            
            if script and script.string:
                jsonld = json.loads(script.string.strip())
                # Normalize using the logic from job_leads.py
                normalized = self.normalize_jobposting(jsonld)
                # Merge normalized data into job_item
                job_item.update(normalized)
            else:
                logger.warning(f"No JSON-LD found for {response.url}")
        except Exception as e:
            logger.error(f"Error parsing job page {response.url}: {e}")

        # Final checks for required fields before yielding
        if not job_item.get('title'):
            job_item['title'] = job_item.get('jobTitle') or 'Unknown Title'
        if not job_item.get('company'):
            job_item['company'] = job_item.get('companyName') or 'Unknown Company'

        yield job_item

    def normalize_jobposting(self, data: dict) -> dict:
        """Ported from job_leads.py"""
        desc_html = data.get("description")
        
        return {
            "external_id": (data.get("identifier") or {}).get("value"),
            "title": data.get("title"),
            "company": (data.get("hiringOrganization") or {}).get("name"),
            "employment_type": data.get("employmentType"),
            "date_posted": data.get("datePosted"),
            "valid_through": data.get("validThrough"),
            "location_raw": {
                "city": (((data.get("jobLocation") or {}).get("address") or {}).get("addressLocality")),
                "region": (((data.get("jobLocation") or {}).get("address") or {}).get("addressRegion")),
                "country": (((data.get("jobLocation") or {}).get("address") or {}).get("addressCountry")),
            },
            "salary_raw": {
                "currency": data.get("salaryCurrency"),
                "min": (((data.get("baseSalary") or {}).get("value") or {}).get("minValue")),
                "max": (((data.get("baseSalary") or {}).get("value") or {}).get("maxValue")),
                "unit": (((data.get("baseSalary") or {}).get("value") or {}).get("unitText")),
            },
            "description_html": desc_html,
        }
