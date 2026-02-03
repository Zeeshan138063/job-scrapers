from supabase import create_client, Client
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class SupabasePipeline:
    """
    Pipeline 4: Save to Supabase
    Handles upserts based on dedup_hash
    """
    
    def __init__(self, supabase_url: str, supabase_key: str, crawler=None):
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.crawler = crawler
        self.client: Optional[Client] = None
        self.stats = {'inserted': 0, 'updated': 0, 'failed': 0}
    
    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            supabase_url=crawler.settings.get('SUPABASE_URL'),
            supabase_key=crawler.settings.get('SUPABASE_KEY'),
            crawler=crawler
        )
    
    def open_spider(self):
        """Initialize Supabase client"""
        if not self.supabase_url or not self.supabase_key:
            logger.warning("Supabase URL or Key missing. SupabasePipeline will be disabled.")
            self.client = None
            return
        
        try:
            self.client = create_client(self.supabase_url, self.supabase_key)
            spider_name = self.crawler.spider.name if self.crawler and self.crawler.spider else "unknown"
            logger.info(f"SupabasePipeline initialized for {spider_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            self.client = None
    
    def close_spider(self):
        """Log final stats"""
        logger.info(
            f"Supabase stats: {self.stats['inserted']} inserted, "
            f"{self.stats['updated']} updated, {self.stats['failed']} failed"
        )
    
    def process_item(self, item):
        """Save item to Supabase"""
        if not self.client:
            return item
        
        try:
            # Prepare data for insert
            job_data = {
                'source': item['source'],
                'external_id': item.get('external_id'),
                'title': item['title'],
                'company': item['company'],
                'location': item.get('location'),
                'location_city': item.get('location_parsed', {}).get('city'),
                'location_state': item.get('location_parsed', {}).get('state'),
                'location_country': item.get('location_parsed', {}).get('country'),
                'salary_raw': item.get('salary'),
                'salary_min': item.get('salary_normalized', {}).get('min') if item.get('salary_normalized') else None,
                'salary_max': item.get('salary_normalized', {}).get('max') if item.get('salary_normalized') else None,
                'salary_currency': item.get('salary_normalized', {}).get('currency') if item.get('salary_normalized') else None,
                'description': item.get('description'),
                'url': item['url'],
                'posted_at': item.get('posted_at'),
                'job_type': item.get('job_type'),
                'remote': item.get('remote', False),
                'experience_level': item.get('experience_level'),
                'scraped_at': item['scraped_at'],
                'dedup_hash': item.get('dedup_hash'),
                'skills': item.get('skills', []),
                'is_active': True
            }
            
            # Upsert (insert or update if exists)
            result = self.client.table('scraper_job_listings').upsert(
                job_data,
                on_conflict='dedup_hash'
            ).execute()
            
            if result.data:
                self.stats['inserted'] += 1
                logger.debug(f"Saved: {item['title']} at {item['company']}")
            else:
                self.stats['updated'] += 1
            
        except Exception as e:
            self.stats['failed'] += 1
            logger.error(f"Failed to save item: {e}")
            logger.error(f"Item data: {dict(item)}")
            # Don't raise - continue processing other items
        
        return item
