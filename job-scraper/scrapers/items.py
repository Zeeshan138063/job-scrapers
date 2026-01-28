import scrapy
from datetime import datetime
from typing import Optional, List, Dict


class JobItem(scrapy.Item):
    """Domain Model: Job Listing"""
    
    # Required fields
    source = scrapy.Field()  # 'linkedin', 'indeed', 'glassdoor'
    external_id = scrapy.Field()  # Unique ID from source
    title = scrapy.Field()
    company = scrapy.Field()
    url = scrapy.Field()
    
    # Optional fields
    location = scrapy.Field()
    location_parsed = scrapy.Field()  # {city, state, country}
    salary = scrapy.Field()
    salary_normalized = scrapy.Field()  # {min, max, currency, period}
    description = scrapy.Field()
    posted_at = scrapy.Field()
    job_type = scrapy.Field()  # full-time, part-time, contract, etc.
    remote = scrapy.Field()  # boolean
    experience_level = scrapy.Field()  # entry, mid, senior
    
    # Enrichment fields
    skills = scrapy.Field()  # List of extracted skills
    benefits = scrapy.Field()  # List of benefits
    
    # Metadata
    scraped_at = scrapy.Field()
    dedup_hash = scrapy.Field()
    raw_html = scrapy.Field()  # For debugging
    
    # Processing metadata
    _processing_start_time = scrapy.Field(serializer=lambda x: None)  # Don't serialize


class ScraperConfigItem(scrapy.Item):
    """Configuration for each spider"""
    spider_name = scrapy.Field()
    enabled = scrapy.Field()
    schedule = scrapy.Field()  # cron expression
    search_queries = scrapy.Field()
    locations = scrapy.Field()
    max_pages = scrapy.Field()
    rate_limit = scrapy.Field()
    use_crawl4ai = scrapy.Field()
    custom_settings = scrapy.Field()
