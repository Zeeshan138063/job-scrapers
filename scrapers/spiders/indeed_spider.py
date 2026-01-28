from scrapers.spiders.base_spider import BaseJobSpider
from urllib.parse import urljoin, quote
import re


class IndeedJobsSpider(BaseJobSpider):
    """
    Indeed Jobs Spider
    Mostly static content, minimal JavaScript
    """
    
    name = 'indeed_jobs'
    source_name = 'indeed'
    config_key = 'indeed'
    allowed_domains = ['indeed.com']
    
    custom_settings = {
        'CONCURRENT_REQUESTS': 5,
        'DOWNLOAD_DELAY': 1,
    }
    
    def build_search_url(self, query: str, location: str, page: int = 0) -> str:
        """Build Indeed search URL"""
        base_url = "https://www.indeed.com/jobs"
        start = page * 10  # Indeed shows ~10-15 jobs per page
        
        params = f"?q={quote(query)}&l={quote(location)}&start={start}"
        return base_url + params
    
    def parse_job_card(self, card, response):
        """Parse job card from Indeed search results"""
        try:
            # Job URL
            job_link = card.css('h2.jobTitle a::attr(href)').get()
            if not job_link:
                return None
            
            full_url = urljoin(response.url, job_link)
            
            # Extract job key (Indeed's ID)
            jk_match = re.search(r'jk=([a-f0-9]+)', full_url)
            external_id = jk_match.group(1) if jk_match else None
            
            # Salary
            salary = card.css('.salary-snippet::text').get()
            
            # Location
            location = card.css('.companyLocation::text').get('').strip()
            
            # Job snippet (short description)
            snippet = ' '.join(card.css('.job-snippet::text').getall()).strip()
            
            return {
                'external_id': external_id,
                'url': full_url,
                'title': card.css('h2.jobTitle span::text').get('').strip(),
                'company': card.css('.companyName::text').get('').strip(),
                'location': location,
                'salary': salary,
                'description': snippet  # Will be enriched in detail page
            }
        except Exception as e:
            self.logger.error(f"Error parsing job card: {e}")
            return None
    
    def parse_job_detail(self, response):
        """Parse Indeed job detail page"""
        try:
            # Full description
            description_parts = response.css('#jobDescriptionText ::text').getall()
            description = ' '.join([p.strip() for p in description_parts if p.strip()])
            
            # Job type
            job_type_elem = response.xpath(
                "//div[contains(text(), 'Job Type')]/following-sibling::div/text()"
            ).get()
            
            # Detect remote
            remote = 'remote' in description.lower()
            
            return {
                'description': description,
                'job_type': self._normalize_job_type(job_type_elem),
                'remote': remote
            }
        except Exception as e:
            self.logger.error(f"Error parsing job detail: {e}")
            return None
    
    def _normalize_job_type(self, text: str) -> str:
        """Normalize job type"""
        if not text:
            return None
        
        text_lower = text.lower()
        if 'full' in text_lower:
            return 'full-time'
        elif 'part' in text_lower:
            return 'part-time'
        elif 'contract' in text_lower:
            return 'contract'
        return text
