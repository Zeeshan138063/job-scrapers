from scrapy.exceptions import DropItem
import redis
import hashlib
import logging

logger = logging.getLogger(__name__)


class DeduplicationPipeline:
    """
    Pipeline 2: Check for duplicates using Redis
    Uses hash of (source + external_id)
    """
    
    def __init__(self, redis_url: str, ttl_days: int = 30, crawler=None):
        self.redis_url = redis_url
        self.ttl_days = ttl_days
        self.crawler = crawler
        self.redis_client = None
        self.stats = {'duplicates': 0, 'new': 0}
    
    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            redis_url=crawler.settings.get('REDIS_URL', 'redis://localhost:6379'),
            ttl_days=
            crawler.settings.get('DEDUP_TTL_DAYS', 30),
            crawler=crawler
        )
    
    def open_spider(self):
        """Initialize Redis connection"""
        self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
        spider_name = self.crawler.spider.name if self.crawler and self.crawler.spider else "unknown"
        logger.info(f"DeduplicationPipeline initialized for {spider_name}")
    
    def close_spider(self):
        """Log stats and close connection"""
        logger.info(
            f"Deduplication stats: {self.stats['new']} new, "
            f"{self.stats['duplicates']} duplicates"
        )
        if self.redis_client:
            self.redis_client.close()
    
    def process_item(self, item, spider):
        """Check if item already exists using a composite key"""
        
        # 1. Collect components for the composite key
        external_id = str(item.get('external_id', ''))
        title = str(item.get('title', '')).lower().strip()
        
        # Location components (depending on item fields)
        region = str(item.get('region') or item.get('location_parsed', {}).get('state', '')).lower().strip()
        country = str(item.get('country_name') or item.get('location_country') or item.get('country_code', '')).lower().strip()
        
        # 2. Create unique hash based on composite key
        # Format: source:id:title:region:country
        dedup_key = f"{item['source']}:{external_id}:{title}:{region}:{country}"
        dedup_hash = hashlib.md5(dedup_key.encode()).hexdigest()
        
        # Store hash in item for database and subsequent pipelines
        item['dedup_hash'] = dedup_hash
        
        # 3. Check Redis for duplicates
        spider_name = self.crawler.spider.name if self.crawler and self.crawler.spider else "unknown"
        redis_key = f"scraped_jobs:{spider_name}"
        
        try:
            if self.redis_client.sismember(redis_key, dedup_hash):
                self.stats['duplicates'] += 1
                logger.info(f"🚫 Duplicate dropped: {item['title']} ({external_id})")
                raise DropItem(f"Duplicate item: {dedup_key}")
            
            # 4. Add to set with TTL (resetting expiry on each addition to keep the set alive)
            self.redis_client.sadd(redis_key, dedup_hash)
            self.redis_client.expire(redis_key, self.ttl_days * 24 * 60 * 60)
        except DropItem:
            raise
        except redis.exceptions.ConnectionError:
            logger.warning("Redis connection failed. Skipping deduplication check.")
        except Exception as e:
            logger.warning(f"Deduplication error: {e}")
        
        # Store hash in item for database
        item['dedup_hash'] = dedup_hash
        
        self.stats['new'] += 1
        return item
