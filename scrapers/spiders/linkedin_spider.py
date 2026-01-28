from scrapers.spiders.base_spider import BaseJobSpider
from urllib.parse import urljoin, quote
import re
from datetime import datetime, timedelta


class LinkedInJobsSpider(BaseJobSpider):
    """
    LinkedIn Jobs Spider
    Requires JavaScript rendering via Crawl4AI
    """
    
    name = 'linkedin_jobs'
    source_name = 'linkedin'
    config_key = 'linkedin'
    allowed_domains = ['linkedin.com']
    
    custom_settings = {
        'CONCURRENT_REQUESTS': 2,
        'DOWNLOAD_DELAY': 3,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 1.0,
    }
    
    def build_search_url(self, query: str, location: str, page: int = 0) -> str:
        """Build LinkedIn search URL"""
        base_url = "https://www.linkedin.com/jobs/search/"
        start = page * 25  # LinkedIn shows 25 jobs per page
        
        params = f"?keywords={quote(query)}&location={quote(location)}&start={start}"
        return base_url + params
    
    def parse_job_card(self, card, response):
        """Parse job card from search results"""
        try:
            # Extract job URL
            job_link = card.css('a.base-card__full-link::attr(href)').get()
            if not job_link:
                return None
            
            # Extract job ID from URL
            job_id_match = re.search(r'/view/(\d+)', job_link)
            external_id = job_id_match.group(1) if job_id_match else None
            
            return {
                'external_id': external_id,
                'url': urljoin(response.url, job_link),
                'title': card.css('.base-search-card__title::text').get('').strip(),
                'company': card.css('.base-search-card__subtitle a::text').get('').strip(),
                'location': card.css('.job-search-card__location::text').get('').strip(),
            }
        except Exception as e:
            self.logger.error(f"Error parsing job card: {e}")
            return None
    
    def parse_job_detail(self, response):
        """Parse LinkedIn job detail page"""
        try:
            # Description
            description_html = response.css('.description__text').get()
            description_text = response.css('.description__text::text').getall()
            description = ' '.join(description_text).strip() if description_text else ''
            
            # Salary (if available)
            salary = response.css('.salary::text').get()
            
            # Job type
            job_type = None
            criteria_items = response.css('.description__job-criteria-item')
            for item in criteria_items:
                header = item.css('.description__job-criteria-subheader::text').get('').strip()
                if 'Employment type' in header:
                    job_type = item.css('.description__job-criteria-text::text').get('').strip()
                    break
            
            # Experience level
            experience_level = None
            for item in criteria_items:
                header = item.css('.description__job-criteria-subheader::text').get('').strip()
                if 'Seniority level' in header:
                    experience_level = item.css('.description__job-criteria-text::text').get('').strip()
                    break
            
            # Posted date
            posted_text = response.css('.posted-time-ago__text::text').get('').strip()
            posted_at = self._parse_relative_date(posted_text)
            
            # Remote work
            remote = 'remote' in description.lower() or 'remote' in response.text.lower()
            
            return {
                'description': description,
                'salary': salary,
                'job_type': self._normalize_job_type(job_type),
                'experience_level': self._normalize_experience_level(experience_level),
                'posted_at': posted_at,
                'remote': remote,
                'raw_html': description_html
            }
        except Exception as e:
            self.logger.error(f"Error parsing job detail: {e}")
            return None
    
    def _parse_relative_date(self, text: str) -> str:
        """Parse relative date like '2 days ago' to ISO format"""
        if not text:
            return None
        
        try:
            # Extract number and unit
            match = re.search(r'(\d+)\s+(minute|hour|day|week|month)s?\s+ago', text.lower())
            if not match:
                return None
            
            amount = int(match.group(1))
            unit = match.group(2)
            
            # Calculate date
            now = datetime.utcnow()
            if unit == 'minute':
                posted = now - timedelta(minutes=amount)
            elif unit == 'hour':
                posted = now - timedelta(hours=amount)
            elif unit == 'day':
                posted = now - timedelta(days=amount)
            elif unit == 'week':
                posted = now - timedelta(weeks=amount)
            elif unit == 'month':
                posted = now - timedelta(days=amount * 30)
            else:
                return None
            
            return posted.isoformat()
        except Exception:
            return None
    
    def _normalize_job_type(self, text: str) -> str:
        """Normalize job type to standard values"""
        if not text:
            return None
        
        text_lower = text.lower()
        if 'full' in text_lower:
            return 'full-time'
        elif 'part' in text_lower:
            return 'part-time'
        elif 'contract' in text_lower:
            return 'contract'
        elif 'intern' in text_lower:
            return 'internship'
        elif 'temporary' in text_lower:
            return 'temporary'
        return text
    
    def _normalize_experience_level(self, text: str) -> str:
        """Normalize experience level"""
        if not text:
            return None
        
        text_lower = text.lower()
        if 'entry' in text_lower or 'associate' in text_lower:
            return 'entry'
        elif 'mid' in text_lower:
            return 'mid'
        elif 'senior' in text_lower or 'lead' in text_lower:
            return 'senior'
        elif 'director' in text_lower or 'executive' in text_lower:
            return 'executive'
        return text
