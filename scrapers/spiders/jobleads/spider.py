import json
import logging

import scrapy

from scrapers.items import JobItem
from scrapers.utils.config_loader import ConfigLoader
from scrapers.utils.credential_manager import CredentialManager
from .client import JobleadsClient
from .constants import countries_dict
from .exceptions import InvalidCredentialsError, AccountBlockedError
from .extractor import JobExtractor
from .mappers import map_listing_response, map_details_response, map_canonical_response, yield_final_item

logger = logging.getLogger(__name__)


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
        'DOWNLOADER_MIDDLEWARES': {
            'scrapers.middlewares.curl_cffi_middleware.CurlCFFIDownloaderMiddleware': 200,
        },
    }

    def __init__(self, country=None, limit=None, search_queries=None, locations=None, *args, **kwargs):
        super(JobLeadsSpider, self).__init__(*args, **kwargs)
        self.country_arg = country.upper() if country else None
        self.limit = int(limit) if limit else None

        # Managers
        self.cm = CredentialManager('config/jobleads_creds.json')
        self.cl = ConfigLoader()

        # Load credentials and configs (Original logic: pass country_arg)
        self.configs = self.cm.get_available_credentials(self.country_arg)

        # Load search queries/locations from DB (Enhanced modular feature)
        self.search_queries = self.cl.get_search_queries("jobleads")
        self.locations_from_db = self.cl.get_locations("jobleads")

        # Override with CLI args if provided
        if search_queries:
            if isinstance(search_queries, str):
                self.search_queries = [search_queries]
            else:
                self.search_queries = search_queries

        if locations:
            if isinstance(locations, str):
                self.locations_from_db = [locations]
            else:
                self.locations_from_db = locations

        # Fallback if both DB and CLI are empty
        if not self.search_queries:
            self.search_queries = [""]
            self.logger.info("Using empty query to fetch all available jobs per country.")

        # Rename for clarity in parser_country
        self.locations = self.locations_from_db

    def start_requests(self):
        if not self.configs:
            self.logger.warning(
                "⚠️ No valid (non-blocked) configurations found to start. Please check jobleads_creds.json.")
            return

        # Target countries (either from argument or from countries_dict)
        if self.country_arg:
            target_countries = {self.country_arg: self.country_arg}
        else:
            target_countries = countries_dict

        total_target = len(target_countries)
        available_accounts = self.configs
        self.logger.info(
            f"🚀 Starting crawl for {total_target} countries using {len(available_accounts)} available accounts.")

        for i, (country_name, country_code) in enumerate(target_countries.items()):
            # Round-robin distribution of accounts across target countries
            account_config = available_accounts[i % len(available_accounts)]
            email = account_config.get('email')
            password = account_config.get('password')

            self.logger.info(f"📍 Country: {country_code} ({country_name}) | Using account: {email}")

            try:
                client = JobleadsClient(email=email, password=password)
                client.refresh_if_needed()

                yield scrapy.Request(
                    url="https://www.jobleads.com",
                    callback=self.parse_country,
                    cb_kwargs={
                        'client': client,
                        'country': country_code,
                        'country_name': country_name,
                        'account_country_code': account_config.get('country_code')
                    },
                    dont_filter=True
                )
            except (InvalidCredentialsError, AccountBlockedError):
                self.logger.error(f"❌ Auth failure for {email} while starting {country_code}. Marking blocked.")
                self._mark_credentials_invalid(account_config.get('country_code'), email, "auth_failure")
            except Exception as e:
                self.logger.error(f"Failed to initialize client for {country_code} with {email}: {e}")

    def parse_country(self, response, client, country, country_name, account_country_code=None):
        self.logger.info(f"📍 Parsing country: {country} ({country_name})")
        try:
            client.refresh_if_needed()
        except (InvalidCredentialsError, AccountBlockedError):
            self.logger.error(f"❌ Auth failed for {country} ({client.email}) in parse_country. Marking blocked.")
            self._mark_credentials_invalid(account_country_code or country, client.email, "mid_crawl_auth_failure")
            return

        for query in self.search_queries:
            payload = {
                "country": country,
                "maxSalary": -1,
                "startIndex": 0,
                "limit": self.limit or 25,
                "filters": {"daysReleased": "1"},
                "query": query
            }
            if self.locations:
                for loc in self.locations:
                    loc_payload = payload.copy()
                    loc_payload["location"] = loc
                    yield self._make_search_request(client, country, country_name, loc_payload, query,
                                                    account_country_code, loc)
            else:
                yield self._make_search_request(client, country, country_name, payload, query, account_country_code)

    def _make_search_request(self, client, country, country_name, payload, query, account_country_code, location=None):
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "user-agent": "Mozilla/5.0",
            "authorization": f"Bearer {client.token}"
        }
        loc_str = f" in {location}" if location else ""
        self.logger.info(f"🔎 Searching for '{query}'{loc_str} in {country}")

        return scrapy.Request(
            url="https://www.jobleads.com/api/v2/search/v2",
            method="POST",
            body=json.dumps(payload),
            headers=headers,
            callback=self.parse_search_results,
            cb_kwargs={
                'client': client,
                'country': country,
                'country_name': country_name,
                'headers': headers,
                'payload': payload,
                'count': 0,
                'query': query,
                'location': location,
                'account_country_code': account_country_code
            },
            meta={
                'use_curl_cffi': True,
                'curl_cffi_session_id': client.email,
                'curl_cffi_cookies': client.get_cookies_dict()
            },
            dont_filter=True
        )

    def parse_search_results(self, response, client, country, country_name, headers, payload, count, query,
                             location=None, account_country_code=None):
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
                        'mapped_listing': mapped_listing,
                        'account_country_code': account_country_code
                    },
                    meta={
                        'use_curl_cffi': True,
                        'curl_cffi_session_id': client.email,
                        'curl_cffi_cookies': client.get_cookies_dict(),
                        'handle_httpstatus_list': [404]
                    },
                    dont_filter=True
                )
                count += 1

            if len(jobs) >= (payload.get('limit') or 25) and (not self.limit or count < self.limit):
                new_payload = payload.copy()
                new_payload["startIndex"] = payload["startIndex"] + len(jobs)

                yield scrapy.Request(
                    url="https://www.jobleads.com/api/v2/search/v2",
                    method="POST",
                    body=json.dumps(new_payload),
                    headers=headers,
                    callback=self.parse_search_results,
                    cb_kwargs={
                        'client': client,
                        'country': country,
                        'country_name': country_name,
                        'headers': headers,
                        'payload': new_payload,
                        'count': count,
                        'query': query,
                        'location': location,
                        'account_country_code': account_country_code
                    },
                    meta={
                        'use_curl_cffi': True,
                        'curl_cffi_session_id': client.email,
                        'curl_cffi_cookies': client.get_cookies_dict()
                    },
                    dont_filter=True
                )
        except (InvalidCredentialsError, AccountBlockedError):
            self.logger.error(f"❌ Auth failed for {country} ({client.email}) in parse_search_results. Marking blocked.")
            self._mark_credentials_invalid(account_country_code or country, client.email, "mid_crawl_auth_failure")
        except Exception as e:
            self.logger.error(f"Error parsing search results for {country}: {e}")

    def parse_job_details(self, response, client, country, country_name, job_id, mapped_listing,
                          account_country_code=None):
        mapped_details = {}
        details_resp = None

        if response.status in (401, 403):
            self.logger.error(
                f"❌ Auth failed (HTTP {response.status}) for {job_id} using {client.email}. Marking blocked.")
            self._mark_credentials_invalid(account_country_code or country, client.email, "http_auth_failure")
            return

        if response.status == 200:
            try:
                details_resp = json.loads(response.text)
                mapped_details = map_details_response(details_resp)
            except Exception as e:
                self.logger.warning(f"Error parsing V1 details for {job_id}: {e}")

        if not mapped_details:
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
                        'mapped_listing': mapped_listing,
                        'account_country_code': account_country_code
                    },
                    meta={
                        'use_curl_cffi': True,
                        'curl_cffi_session_id': client.email,
                        'curl_cffi_cookies': client.get_cookies_dict(),
                        'handle_httpstatus_list': [404]
                    },
                    dont_filter=True
                )
                return
            else:
                self.logger.warning(f"Both V1 and V3 failed for {job_id}")

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
                    meta={
                        'use_curl_cffi': True,
                        'curl_cffi_session_id': client.email,
                        'curl_cffi_cookies': client.get_cookies_dict()
                    },
                    dont_filter=True
                )
                return

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
        item_dict = yield_final_item(listing, details, canonical, country_name)
        yield JobItem(**item_dict)

    def _mark_credentials_invalid(self, country_code, email, reason):
        self.logger.info(f"🚩 Marking credentials as blocked: {email} ({country_code}) - Reason: {reason}")
        self.cm.mark_blocked(country_code, email, reason)
