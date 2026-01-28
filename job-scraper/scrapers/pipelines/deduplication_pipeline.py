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
    
    def __init__(self, redis_url: str, ttl_days: int = 30):
        self.redis_url = redis_url
        self.ttl_days = ttl_days
        self.redis_client = None
        self.stats = {'duplicates': 0, 'new': 0}
    
    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            redis_url=crawler.settings.get('REDIS_URL', 'redis://localhost:6379'),
            ttl_days=crawler.settings.get('DEDUP_TTL_DAYS', 30)
        )
    
    def open_spider(self, spider):
        """Initialize Redis connection"""
        self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
        logger.info(f"DeduplicationPipeline initialized for {spider.name}")
    
    def close_spider(self, spider):
        """Log stats and close connection"""
        logger.info(
            f"Deduplication stats: {self.stats['new']} new, "
            f"{self.stats['duplicates']} duplicates"
        )
        if self.redis_client:
            self.redis_client.close()
    
    def process_item(self, item, spider):
        """Check if item already exists"""
        
        # Create unique hash
        dedup_key = f"{item['source']}:{item['external_id']}"
        dedup_hash = hashlib.md5(dedup_key.encode()).hexdigest()
        
        # Check Redis set
        redis_key = f"scraped_jobs:{spider.name}"
        
        if self.redis_client.sismember(redis_key, dedup_hash):
            self.stats['duplicates'] += 1
            logger.debug(f"Duplicate: {item['title']} from {item['company']}")
            raise DropItem(f"Duplicate item: {dedup_key}")
        
        # Add to set with TTL
        self.redis_client.sadd(redis_key, dedup_hash)
        self.redis_client.expire(redis_key, self.ttl_days * 24 * 60 * 60)
        
        # Store hash in item for database
        item['dedup_hash'] = dedup_hash
        
        self.stats['new'] += 1
        return item
