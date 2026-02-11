from datetime import datetime
from typing import Optional, List, Dict
from sqlmodel import SQLModel, Field, Column, JSON
from sqlalchemy import ARRAY, String

class SpiderConfig(SQLModel, table=True):
    __tablename__ = "scraper_spider_configs"
    
    spider_id: str = Field(primary_key=True)
    is_active: bool = Field(default=True)
    cron_schedule: str = Field(default="0 */4 * * *")
    
    # Search Parameters
    search_queries: List[str] = Field(sa_column=Column(ARRAY(String)))
    locations: List[str] = Field(sa_column=Column(ARRAY(String)))
    max_pages: int = Field(default=5)
    
    # Performance / Scrapy Settings
    concurrent_requests: int = Field(default=2)
    download_delay: float = Field(default=2.0)
    use_crawl4ai: bool = Field(default=False)
    
    filters: Dict = Field(default={}, sa_column=Column(JSON))
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class FilterDefinition(SQLModel, table=True):
    __tablename__ = "scraper_filter_definitions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    spider_id: str = Field(foreign_key="scraper_spider_configs.spider_id", ondelete="CASCADE")
    filter_key: str
    display_name: Optional[str] = None
    filter_type: str = Field(default="select") # select, text, number, boolean
    is_nested: bool = Field(default=False)
    default_value: Optional[str] = None
    is_required: bool = Field(default=False)
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class FilterOption(SQLModel, table=True):
    __tablename__ = "scraper_filter_options"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    filter_definition_id: int = Field(foreign_key="scraper_filter_definitions.id", ondelete="CASCADE")
    option_label: str
    option_value: str
    group_name: Optional[str] = None
    extra_metadata: Dict = Field(default={}, sa_column=Column("metadata", JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)

class JobListing(SQLModel, table=True):
    __tablename__ = "scraper_job_listings"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    source: str
    external_id: Optional[str] = None
    title: str
    company: str
    location: Optional[str] = None
    location_city: Optional[str] = None
    location_state: Optional[str] = None
    location_country: Optional[str] = None
    salary_raw: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: Optional[str] = None
    description: Optional[str] = None
    url: str
    posted_at: Optional[datetime] = None
    job_type: Optional[str] = None
    remote: bool = Field(default=False)
    experience_level: Optional[str] = None
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
    dedup_hash: str = Field(unique=True, index=True)
    skills: List[str] = Field(default=[], sa_column=Column(ARRAY(String)))
    is_active: bool = Field(default=True)
    
    # Staging meta
    is_exported: bool = Field(default=False)
    exported_at: Optional[datetime] = None

class SpiderRun(SQLModel, table=True):
    __tablename__ = "scraper_runs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    spider_name: str
    status: str # running, completed, failed
    duration_seconds: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    items_scraped: int = Field(default=0)
    errors_count: int = Field(default=0)
    metadata_json: Dict = Field(default={}, sa_column=Column(JSON))

class ScrapeRequest(SQLModel):
    spider_id: str
    search_queries: List[str]
    locations: Optional[List[str]] = None
    max_pages: Optional[int] = 5
    concurrent_requests: Optional[int] = 2
    filters: Optional[Dict] = {}
