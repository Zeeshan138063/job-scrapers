from datetime import datetime
from typing import Optional, List, Dict
from sqlmodel import SQLModel, Field, Column, text, DateTime, UniqueConstraint, JSON
from sqlalchemy.dialects.postgresql import JSONB, TEXT, ARRAY, UUID
from sqlalchemy import String

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
    use_crawl4ai: bool = Field(default=False)
    retry_on_auth_failure: bool = Field(default=True)
    
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
    __tablename__ = "job_listings"
    
    id: Optional[str] = Field(
        default=None, 
        sa_column=Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    )
    source: str
    external_id: str = Field(index=True)
    source_domain: str = Field(index=True)
    url: Optional[str] = None
    source_url: Optional[str] = None
    title: str
    company_name: Optional[str] = None
    location_raw: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    country_code: Optional[str] = None
    employment_type: Optional[str] = None
    remote_modality: Optional[str] = None
    salary_raw: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: Optional[str] = None
    salary_period: Optional[str] = None
    description_short: Optional[str] = None
    description_html: Optional[str] = None
    description_text: Optional[str] = None
    
    # Structured Data (JSONB)
    benefits: Dict = Field(default={}, sa_column=Column(JSONB))
    skills: Dict = Field(default={}, sa_column=Column(JSONB))
    qualifications: Dict = Field(default={}, sa_column=Column(JSONB))
    responsibilities: Dict = Field(default={}, sa_column=Column(JSONB))
    education: Dict = Field(default={}, sa_column=Column(JSONB))
    tools: Dict = Field(default={}, sa_column=Column(JSONB))
    meta_flags: Dict = Field(default={}, sa_column=Column(JSONB, server_default=text("'{}'::jsonb")))
    
    scraped_source: Optional[str] = None
    hostname_origin: Optional[str] = None
    raw_data: Dict = Field(default={}, sa_column=Column(JSONB))
    
    posted_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    last_scraped_at: datetime = Field(sa_column=Column(DateTime(timezone=True), server_default=text("now()")))
    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True), server_default=text("now()")))
    updated_at: datetime = Field(sa_column=Column(DateTime(timezone=True), server_default=text("now()")))
    country_name: Optional[str] = None
    
    # Unique constraint (not the primary key, but identifying)
    __table_args__ = (
        UniqueConstraint("external_id", "source_domain", name="job_listings_external_id_source_domain_key1"),
    )

class SpiderRun(SQLModel, table=True):
    __tablename__ = "scraper_runs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    spider_name: str
    status: str # running, completed, failed
    duration_seconds: Optional[float] = None
    human_duration: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    items_scraped: int = Field(default=0)
    errors_count: int = Field(default=0)
    metadata_json: Dict = Field(default={}, sa_column=Column(JSON))
