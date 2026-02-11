import os
import logging
from sqlmodel import Session, create_engine, select
from api.models import JobListing
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
                    existing.company = item['company']
                    existing.location = item.get('location')
                    existing.salary_raw = item.get('salary')
                    existing.description = item.get('description')
                    existing.scraped_at = item.get('scraped_at')
                    session.add(existing)
                    self.stats['updated'] += 1
                else:
                    # Create new
                    job = JobListing(
                        source=item['source'],
                        external_id=item.get('external_id'),
                        title=item['title'],
                        company=item['company'],
                        location=item.get('location'),
                        location_city=item.get('location_parsed', {}).get('city'),
                        location_state=item.get('location_parsed', {}).get('state'),
                        location_country=item.get('location_parsed', {}).get('country'),
                        salary_raw=item.get('salary'),
                        url=item['url'],
                        description=item.get('description'),
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
