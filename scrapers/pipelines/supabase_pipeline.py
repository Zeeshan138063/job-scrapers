import os
import logging
from typing import Optional
from supabase import create_client, Client
from scrapy.exceptions import NotConfigured

logger = logging.getLogger(__name__)

class SupabasePipeline:
    """
    Pipeline to save scraped items to a Supabase table for testing/verification.
    """
    
    def __init__(self, supabase_url: str, supabase_key: str):
        if not supabase_url or not supabase_key:
            raise NotConfigured("Supabase URL or Key not set.")
            
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.client: Optional[Client] = None
        self.stats = {'upserted': 0, 'failed': 0}
        
    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            supabase_url=crawler.settings.get('SUPABASE_URL') or os.getenv('SUPABASE_URL'),
            supabase_key=crawler.settings.get('SUPABASE_KEY') or os.getenv('SUPABASE_KEY')
        )
        
    def open_spider(self, spider):
        try:
            self.client = create_client(self.supabase_url, self.supabase_key)
            logger.info("SupabasePipeline connected to Supabase")
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {e}")
            raise NotConfigured(f"Supabase connection failed: {e}")
            
    def process_item(self, item, spider):
        if not self.client:
            return item
            
        company = item.get("company_name") or item.get("company")
        logger.info(f"SupabasePipeline processing: {item.get('title')} at {company}")
        
        # Prepare payload for Supabase
        # Map fields to match the job_listings table schema in Supabase
        
        # Priority 1: Use raw_data if already populated by the spider/previous pipelines
        # Priority 2: Fallback to building it from individual raw fields
        raw_data = item.get("raw_data")
        if not raw_data:
            raw_data = {
                 "listing": item.get("_raw_listing", {}),
                 "details": item.get("_raw_details", {}),
                 "canonical": item.get("_raw_canonical", {})
            }

        payload = {
            "external_id": item.get("external_id"),
            "source_domain": item.get("source_domain", "jobleads.com"),
            "url": item.get("url"),
            "source_url": item.get("source_url"),
            "title": item.get("title"),
            "company_name": company,
            "location_raw": item.get("location"),
            "city": item.get("location_parsed", {}).get("city"),
            "region": item.get("region") or item.get("location_parsed", {}).get("state"),
            "country_code": item.get("country_code"),
            "country_name": item.get("country_name"),
            "employment_type": item.get("employment_type"),
            "remote_modality": item.get("remote_modality"),
            "salary_raw": item.get("salary_raw"),
            "salary_min": item.get("salary_min"),
            "salary_max": item.get("salary_max"),
            "salary_currency": item.get("salary_currency"),
            "salary_period": item.get("salary_period"),
            "description_short": item.get("description_short"),
            "description_html": item.get("description_html"),
            "description_text": item.get("description_text"),
            "benefits": item.get("benefits"),
            "skills": item.get("skills"),
            "qualifications": item.get("qualifications"),
            "responsibilities": item.get("responsibilities"),
            "education": item.get("education"),
            "tools": item.get("tools"),
            "meta_flags": item.get("meta_flags"),
            "scraped_source": item.get("scraped_source") or item.get("source"),
            "hostname_origin": item.get("hostname_origin"),
            "raw_data": raw_data,
            "posted_at": item.get("posted_at"),
            "expires_at": item.get("expires_at"),
            "last_scraped_at": item.get("scraped_at")
        }

        try:
            # Upsert into job_listings table
            # Assuming external_id and source_domain form a unique constraint
            logger.debug(f"Upserting payload to Supabase: {payload.get('external_id')} (Country: {payload.get('country_name')})")
            
            # Some schemas might use scraper_job_listings, others job_listings
            # Based on logs, job_listings is currently active
            table_name = "job_listings"
            
            response = self.client.table(table_name).upsert(
                payload, 
                on_conflict="external_id, source_domain"
            ).execute()
            
            self.stats['upserted'] += 1
            logger.info(f"✅ Supabase upserted: {item.get('title')} from {company}")
        except Exception as e:
            logger.error(f"SupabasePipeline error for {item.get('external_id')}: {str(e)}")
            # Log more details if it's a Postgrest error
            if hasattr(e, 'message'):
                logger.error(f"Postgrest message: {e.message}")
            if hasattr(e, 'details'):
                logger.error(f"Postgrest details: {e.details}")
            if hasattr(e, 'hint'):
                logger.error(f"Postgrest hint: {e.hint}")
            self.stats['failed'] += 1
            
        return item
        
    def close_spider(self, spider):
        logger.info(f"Supabase stats: {self.stats}")
