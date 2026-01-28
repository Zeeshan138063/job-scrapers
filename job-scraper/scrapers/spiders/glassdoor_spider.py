from scrapers.spiders.base_spider import BaseJobSpider
from urllib.parse import urljoin, quote
import re


class GlassdoorJobsSpider(BaseJobSpider):
    """
    Glassdoor Jobs Spider
    Requires JavaScript rendering
    """
    
    name = 'glassdoor_jobs'
    source_name = 'glassdoor'
    config_key = 'glassdoor'
    allowed_domains = ['glassdoor.com']
    
    custom_settings = {
        'CONCURRENT_REQUESTS': 2,
        'DOWNLOAD_DELAY': 4,
        'AUTOTHROTTLE_ENABLED': True,
    }
    
    def build_search_url(self, query: str, location: str, page: int = 0) -> str:
        """Build Glassdoor search URL"""
        base_url = "https://www.glassdoor.com/Job/jobs.htm"
        page_num = page + 1
        
        params = f"?sc.keyword={quote(query)}&locT=C&locId={quote(location)}&ip={page_num}"
        return base_url + params
    
    def parse_job_card(self, card, response):
        """Parse job card from Glassdoor search results"""
        try:
            # Job URL
            job_link = card.css('a.jobLink::attr(href)').get()
            if not job_link:
                return None
            
            full_url = urljoin('https://www.glassdoor.com', job_link)
            
            # Extract job ID
            job_id_match = re.search(r'jobListingId=(\d+)', full_url)
            external_id = job_id_match.group(1) if job_id_match else None
            
            # Salary estimate
            salary = card.css('.salaryEstimate::text').get()
            
            return {
                'external_id': external_id,
                'url': full_url,
                'title': card.css('.jobTitle::text').get('').strip(),
                'company': card.css('.jobHeader .employerName::text').get('').strip(),
                'location': card.css('.location::text').get('').strip(),
                'salary': salary
            }
        except Exception as e:
            self.logger.error(f"Error parsing job card: {e}")
            return None
    
    def parse_job_detail(self, response):
        """Parse Glassdoor job detail page"""
        try:
            # Description
            description_parts = response.css('.jobDescriptionContent ::text').getall()
            description = ' '.join([p.strip() for p in description_parts if p.strip()])
            
            # Job type (if available)
            job_type = response.css('.jobType::text').get()
            
            # Remote
            remote = 'remote' in description.lower()
            
            return {
                'description': description,
                'job_type': job_type,
                'remote': remote
            }
        except Exception as e:
            self.logger.error(f"Error parsing job detail: {e}")
            return None
