import os
import logging
from datetime import datetime, timezone
from sqlmodel import Session, create_engine, select, and_
from scrapers.models import JobListing

logger = logging.getLogger(__name__)

class PostgresPipeline:
    """
    Pipeline to save scraped items to the dedicated PostgreSQL database.
    Acts as a pure storage sink, using (external_id, source_domain) for upsert.
    With enhanced logging for debugging.
    """
    
    def __init__(self, database_url: str, pool_size: int = 3, max_overflow: int = 5,
                 pool_timeout: int = 30, pool_recycle: int = 1800):
        self.database_url = database_url
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout
        self.pool_recycle = pool_recycle
        self.engine = None
        self.stats = {'inserted': 0, 'updated': 0, 'failed': 0}
        logger.debug(f"PostgresPipeline initialized with URL: {database_url}")
    
    @classmethod
    def from_crawler(cls, crawler):
        s = crawler.settings
        db_url = s.get('DATABASE_URL') or os.getenv('DATABASE_URL')
        logger.info(f"PostgresPipeline: Loading DATABASE_URL: {'set' if db_url else 'NOT SET'}")
        pipeline = cls(
            database_url=db_url,
            pool_size=int(s.get('DB_POOL_SIZE') or os.getenv('DB_POOL_SIZE', 3)),
            max_overflow=int(s.get('DB_POOL_MAX_OVERFLOW') or os.getenv('DB_POOL_MAX_OVERFLOW', 5)),
            pool_timeout=int(s.get('DB_POOL_TIMEOUT') or os.getenv('DB_POOL_TIMEOUT', 30)),
            pool_recycle=int(s.get('DB_POOL_RECYCLE') or os.getenv('DB_POOL_RECYCLE', 1800)),
        )
        pipeline.crawler = crawler
        return pipeline
    
    def open_spider(self, spider=None):
        if not self.database_url:
            logger.error("❌ PostgresPipeline: DATABASE_URL not set. Pipeline disabled.")
            return
            
        try:
            self.engine = create_engine(
                self.database_url,
                pool_size=self.pool_size,
                max_overflow=self.max_overflow,
                pool_timeout=self.pool_timeout,
                pool_recycle=self.pool_recycle,
                pool_pre_ping=True,
            )
            # Test connection
            with self.engine.connect() as conn:
                logger.info("✅ PostgresPipeline successfully connected and verified database connection.")
        except Exception as e:
            logger.error(f"❌ PostgresPipeline: Failed to connect to Postgres: {e}")
            self.engine = None
            
    def process_item(self, item, spider=None):
        if not self.engine:
            logger.warning("⚠️ PostgresPipeline skipping item: No database engine.")
            return item
            
        external_id = item.get('external_id')
        source_domain = item.get('source_domain')
        
        if not external_id or not source_domain:
            logger.warning(f"⚠️ PostgresPipeline: Item missing external_id ({external_id}) or source_domain ({source_domain}). Skipping.")
            return item
            
        logger.info(f"💾 PostgresPipeline processing: {item.get('title')} ({external_id})")
        
        try:
            # 1. Filter item fields to match JobListing model
            listing_data = self._filter_listing_data(item)
            logger.debug(f"Filtered listing data keys: {list(listing_data.keys())}")
            
            with Session(self.engine) as session:
                # 2. Check for existing record by (external_id, source_domain)
                statement = select(JobListing).where(
                    and_(
                        JobListing.external_id == external_id,
                        JobListing.source_domain == source_domain
                    )
                )
                existing = session.exec(statement).first()
                
                if existing:
                    logger.debug(f"Updating existing record: {existing.id}")
                    # Update dynamic fields
                    for key, value in listing_data.items():
                        if key != 'id': # Don't update PK
                            setattr(existing, key, value)
                    existing.updated_at = datetime.now(timezone.utc)
                    session.add(existing)
                    self.stats['updated'] += 1
                else:
                    logger.debug("Creating new record")
                    # Create new record
                    job = JobListing(**listing_data)
                    session.add(job)
                    self.stats['inserted'] += 1
                
                session.commit()
                logger.debug("Transaction committed successfully")
        except Exception as e:
            logger.error(f"❌ PostgresPipeline error during storage: {e}")
            self.stats['failed'] += 1
            
        return item
    
    def _filter_listing_data(self, item: dict) -> dict:
        """
        Filters the item dictionary to only include keys that are valid fields
        in the JobListing model.
        """
        # Handle Pydantic v1 and v2 field identification
        if hasattr(JobListing, 'model_fields'):
            valid_fields = JobListing.model_fields.keys()
        elif hasattr(JobListing, '__fields__'):
            valid_fields = JobListing.__fields__.keys()
        else:
            valid_fields = list(item.keys())
        
        filtered = {}
        # Basic mapping for fields that might have different names in items
        mapping = {
            'company': 'company_name',
            'location': 'location_raw',
            'country_name': 'country_name',
            'source': 'source',
            'scraped_at': 'last_scraped_at'
        }
        
        for key in item:
            target_key = mapping.get(key, key)
            if target_key in valid_fields and target_key != 'id':
                filtered[target_key] = item[key]
                
        # Specialized handling for location_parsed if present
        if 'location_parsed' in item:
            lp = item['location_parsed']
            if 'city' in valid_fields and not filtered.get('city'): filtered['city'] = lp.get('city')
            if 'region' in valid_fields and not filtered.get('region'): filtered['region'] = lp.get('state') or lp.get('region')
            if 'country_code' in valid_fields and not filtered.get('country_code'): filtered['country_code'] = lp.get('country')

        return filtered

    def close_spider(self, spider=None):
        logger.info(f"📊 Postgres Final Stats: {self.stats}")
