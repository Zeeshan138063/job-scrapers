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
    company_name = scrapy.Field()
    country_name = scrapy.Field()
    url = scrapy.Field()
    
    # Optional fields
    location = scrapy.Field()
    location_parsed = scrapy.Field()  # {city, state, country}
    location_city = scrapy.Field()
    location_state = scrapy.Field()
    location_country = scrapy.Field()
    region = scrapy.Field()
    country_code = scrapy.Field()
    salary = scrapy.Field()
    salary_raw = scrapy.Field()
    salary_min = scrapy.Field()
    salary_max = scrapy.Field()
    salary_currency = scrapy.Field()
    salary_period = scrapy.Field()
    salary_normalized = scrapy.Field()  # {min, max, currency, period}
    description = scrapy.Field()
    description_html = scrapy.Field()
    description_text = scrapy.Field()
    description_short = scrapy.Field()
    posted_at = scrapy.Field()
    expires_at = scrapy.Field()
    job_type = scrapy.Field()  # full-time, part-time, contract, etc.
    employment_type = scrapy.Field()
    remote = scrapy.Field()  # boolean
    remote_modality = scrapy.Field()
    experience_level = scrapy.Field()  # entry, mid, senior
    benefits = scrapy.Field()  # List of benefits
    qualifications = scrapy.Field()
    responsibilities = scrapy.Field()
    skills = scrapy.Field()  # List of extracted skills
    education = scrapy.Field()
    tools = scrapy.Field()
    
    # Storage Metadata
    source_domain = scrapy.Field()
    source_url = scrapy.Field()
    hostname_origin = scrapy.Field()
    location_raw = scrapy.Field()
    meta_flags = scrapy.Field()
    scraped_source = scrapy.Field()
    
    # Metadata
    scraped_at = scrapy.Field()
    raw_data = scrapy.Field()
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
