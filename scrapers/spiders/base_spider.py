import scrapy
import yaml
import os
from abc import abstractmethod
from datetime import datetime
from typing import Dict, List, Optional
from supabase import create_client

from supabase import create_client



class BaseJobSpider(scrapy.Spider):
    """
    Base spider with configuration loading and common utilities
    Template Method Pattern
    """
    
    # Override in subclasses
    source_name: str = None
    config_key: str = None
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Load spider configuration
        self.config = self._load_config()
        
        # Extract settings
        self.search_queries = self._get_arg_or_config('search_queries', ['python developer'])
        self.locations = self._get_arg_or_config('locations', ['United States'])
        self.max_pages = self._get_arg_or_config('max_pages', 5)
        
        self.logger.info(f"Initialized {self.name} with config: {self.config}")
    
    def _load_config(self) -> Dict:
        """Load spider configuration from Supabase (preferred) or YAML (fallback)"""
        # Try Supabase first
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        if supabase_url and supabase_key:
            try:
                client = create_client(supabase_url, supabase_key)
                response = client.table('scraper_spider_configs').select('*').eq('spider_id', self.name).execute()
                if response.data:
                    db_config = response.data[0]
                    self.logger.info(f"Loaded config from Supabase for {self.name}")
                    return db_config
            except Exception as e:
                self.logger.error(f"Failed to load config from Supabase: {e}")

        # Fallback to YAML
        config_path = os.getenv('SPIDER_CONFIG_PATH', '/app/config/spiders.yml')
        try:
            with open(config_path, 'r') as f:
                all_configs = yaml.safe_load(f)
                return all_configs.get(self.config_key, {})
        except FileNotFoundError:
            self.logger.warning(f"Config file not found: {config_path}, using defaults")
            return {}
    
    def _get_arg_or_config(self, key: str, default):
        """Get value from spider args or config file"""
        # Priority: 1. Spider args, 2. Config file, 3. Default
        return getattr(self, key, self.config.get(key, default))
    
    @abstractmethod
    def build_search_url(self, query: str, location: str, page: int = 0) -> str:
        """Build search URL - implement in subclass"""
        pass
    
    @abstractmethod
    def parse_job_card(self, card, response) -> Optional[Dict]:
        """Parse job card from search results - implement in subclass"""
        pass
    
    @abstractmethod
    def parse_job_detail(self, response) -> Optional[Dict]:
        """Parse job detail page - implement in subclass"""
        pass
    
    def start_requests(self):
        """Generate initial requests"""
        for query in self.search_queries:
            for location in self.locations:
                for page in range(self.max_pages):
                    url = self.build_search_url(query, location, page)
                    
                    yield scrapy.Request(
                        url=url,
                        callback=self.parse_search_page,
                        errback=self.handle_error,
                        meta={
                            'search_query': query,
                            'location': location,
                            'page': page,
                            'use_crawl4ai': self.config.get('use_crawl4ai', False),
                            'wait_for': self.config.get('wait_for_selector'),
                            'proxy': self.config.get('use_proxy', False)
                        }
                    )
    
    def parse_search_page(self, response):
        """Parse search results page - common logic"""
        job_cards = response.css(self.config.get('job_card_selector', '.job-card'))
        
        self.logger.info(
            f"Found {len(job_cards)} jobs on page {response.meta['page']} "
            f"for query '{response.meta['search_query']}' in {response.meta['location']}"
        )
        
        for card in job_cards:
            job_data = self.parse_job_card(card, response)
            
            if job_data and job_data.get('url'):
                # Follow to detail page if configured
                if self.config.get('scrape_detail_pages', True):
                    yield scrapy.Request(
                        url=job_data['url'],
                        callback=self.parse_detail_wrapper,
                        errback=self.handle_error,
                        meta={
                            **response.meta,
                            'base_data': job_data,
                            'use_crawl4ai': self.config.get('detail_use_crawl4ai', False),
                            'wait_for': self.config.get('detail_wait_for_selector')
                        }
                    )
                else:
                    # Yield job from search page only
                    yield self._create_job_item(job_data)
    
    def parse_detail_wrapper(self, response):
        """Wrapper for detail page parsing"""
        base_data = response.meta.get('base_data', {})
        detail_data = self.parse_job_detail(response)
        
        if detail_data:
            # Merge base data with detail data
            merged_data = {**base_data, **detail_data}
            yield self._create_job_item(merged_data)
    
    def _create_job_item(self, data: Dict):
        """Create JobItem from parsed data"""
        from scrapers.items import JobItem
        
        item = JobItem()
        
        # Required fields
        item['source'] = self.source_name
        item['external_id'] = data.get('external_id')
        item['title'] = data.get('title')
        item['company'] = data.get('company')
        item['url'] = data.get('url')
        
        # Optional fields
        item['location'] = data.get('location')
        item['salary'] = data.get('salary')
        item['description'] = data.get('description')
        item['posted_at'] = data.get('posted_at')
        item['job_type'] = data.get('job_type')
        item['remote'] = data.get('remote')
        item['experience_level'] = data.get('experience_level')
        
        # Metadata
        item['scraped_at'] = datetime.utcnow().isoformat()
        item['_processing_start_time'] = datetime.utcnow().timestamp()
        
        return item
    
    def handle_error(self, failure):
        """Common error handling"""
        self.logger.error(f"Request failed: {failure.request.url}")
        self.logger.error(f"Reason: {failure.value}")
        
        # Track error in metrics
        if hasattr(self, 'crawler') and self.crawler.stats:
            self.crawler.stats.inc_value(f'errors/{failure.type.__name__}')
