import os
import logging
from sqlmodel import Session, create_engine, select
from scrapers.models import JobListing
import hashlib

logger = logging.getLogger(__name__)

class PostgresPipeline:
    """
    Pipeline to save scraped items to the dedicated PostgreSQL staging database.
    """
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = None
        self.stats = {'inserted': 0, 'updated': 0, 'failed': 0}
    
    @classmethod
    def from_crawler(cls, crawler):
        pipeline = cls(
            database_url=crawler.settings.get('DATABASE_URL') or os.getenv('DATABASE_URL')
        )
        pipeline.crawler = crawler
        return pipeline
    
    def open_spider(self, spider=None):
        if not self.database_url:
            logger.error("DATABASE_URL not set. PostgresPipeline disabled.")
            return
            
        try:
            self.engine = create_engine(self.database_url)
            logger.info("PostgresPipeline connected to staging database")
        except Exception as e:
            logger.error(f"Failed to connect to Postgres: {e}")
            self.engine = None
            
    def process_item(self, item, spider=None):
        if not self.engine:
            return item
            
        try:
            with Session(self.engine) as session:
                # Calculate dedup_hash if not provided
                if not item.get('dedup_hash'):
                    unique_str = f"{item['source']}:{item.get('external_id') or item['url']}"
                    item['dedup_hash'] = hashlib.md5(unique_str.encode()).hexdigest()
                
                # Check for existing
                statement = select(JobListing).where(JobListing.dedup_hash == item['dedup_hash'])
                existing = session.exec(statement).first()
                
                if existing:
                    # Update fields
                    existing.title = item['title']
                    existing.company_name = item.get('company_name') or item.get('company')
                    existing.country_name = item.get('country_name')
                    existing.location = item.get('location')
                    existing.salary_raw = item.get('salary') or item.get('salary_raw')
                    existing.salary_min = item.get('salary_min')
                    existing.salary_max = item.get('salary_max')
                    existing.salary_currency = item.get('salary_currency')
                    existing.salary_period = item.get('salary_period')
                    existing.description = item.get('description')
                    existing.description_short = item.get('description_short')
                    existing.description_html = item.get('description_html')
                    existing.description_text = item.get('description_text')
                    existing.employment_type = item.get('employment_type')
                    existing.remote_modality = item.get('remote_modality')
                    existing.source_url = item.get('source_url')
                    existing.benefits = item.get('benefits', {})
                    existing.qualifications = item.get('qualifications', {})
                    existing.responsibilities = item.get('responsibilities', {})
                    existing.education = item.get('education', {})
                    existing.tools = item.get('tools', {})
                    existing.meta_flags = item.get('meta_flags', {})
                    existing.hostname_origin = item.get('hostname_origin')
                    existing.scraped_at = item.get('scraped_at')
                    session.add(existing)
                    self.stats['updated'] += 1
                else:
                    # Create new
                    job = JobListing(
                        source=item['source'],
                        external_id=item.get('external_id'),
                        source_domain=item.get('source_domain'),
                        title=item['title'],
                        company_name=item.get('company_name') or item.get('company'),
                        country_name=item.get('country_name'),
                        location=item.get('location'),
                        location_city=item.get('location_parsed', {}).get('city'),
                        location_state=item.get('location_parsed', {}).get('state'),
                        location_country=item.get('location_parsed', {}).get('country'),
                        salary_raw=item.get('salary') or item.get('salary_raw'),
                        salary_min=item.get('salary_min'),
                        salary_max=item.get('salary_max'),
                        salary_currency=item.get('salary_currency'),
                        salary_period=item.get('salary_period'),
                        url=item['url'],
                        source_url=item.get('source_url'),
                        employment_type=item.get('employment_type'),
                        remote_modality=item.get('remote_modality'),
                        description=item.get('description'),
                        description_short=item.get('description_short'),
                        description_html=item.get('description_html'),
                        description_text=item.get('description_text'),
                        benefits=item.get('benefits', {}),
                        qualifications=item.get('qualifications', {}),
                        responsibilities=item.get('responsibilities', {}),
                        education=item.get('education', {}),
                        tools=item.get('tools', {}),
                        meta_flags=item.get('meta_flags', {}),
                        hostname_origin=item.get('hostname_origin'),
                        dedup_hash=item['dedup_hash'],
                        scraped_at=item.get('scraped_at'),
                    )
                    session.add(job)
                    self.stats['inserted'] += 1
                
                session.commit()
        except Exception as e:
            logger.error(f"PostgresPipeline error: {e}")
            self.stats['failed'] += 1
            
        return item
    
    def close_spider(self, spider=None):
        logger.info(f"Postgres stats: {self.stats}")
