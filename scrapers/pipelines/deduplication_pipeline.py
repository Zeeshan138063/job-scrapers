from scrapy.exceptions import DropItem
import redis
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
    
        # 1. Use composite key (source_domain + external_id)
        external_id = item.get('external_id')
        source_domain = item.get('source_domain')
        
        if not external_id or not source_domain:
            logger.warning(f"Item missing external_id or source_domain: {item.get('title')}")
            return item
            
        dedup_key = f"job:{source_domain}:{external_id}"
        
        # 3. Check Redis for duplicates
        try:
            # Check if exists in Redis
            if self.redis_client.sismember(self.redis_key, dedup_key):
                self.stats['duplicates'] += 1
                logger.info(f"🚫 Duplicate dropped: {item['title']} ({external_id})")
                raise DropItem(f"Duplicate item found: {dedup_key}")
            
            # Add to set
            self.redis_client.sadd(self.redis_key, dedup_key)
            # 4. Add to set with TTL (resetting expiry on each addition to keep the set alive)
            self.redis_client.expire(self.redis_key, self.ttl_days * 24 * 60 * 60)
        except DropItem:
            raise
        except redis.exceptions.ConnectionError:
            logger.warning("Redis connection failed. Skipping deduplication check.")
        except Exception as e:
            logger.warning(f"Deduplication error: {e}")
        
        
        self.stats['new'] += 1
        return item
