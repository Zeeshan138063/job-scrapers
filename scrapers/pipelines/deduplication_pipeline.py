import logging

import redis
from scrapy.exceptions import DropItem

logger = logging.getLogger(__name__)


class DeduplicationPipeline:
    """
    Pipeline 2: Check for duplicates using Redis
    Uses hash of (source_domain + external_id)
    """
    
    def __init__(self, redis_url: str, ttl_days: int = 30, crawler=None):
        self.redis_url = redis_url
        self.ttl_days = ttl_days
        self.crawler = crawler
        self.redis_client = None
        self.redis_key = None
        self.stats = {'duplicates': 0, 'new': 0}
    
    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            redis_url=crawler.settings.get('REDIS_URL', 'redis://localhost:6379'),
            ttl_days=crawler.settings.get('DEDUP_TTL_DAYS', 30),
            crawler=crawler
        )

    def open_spider(self, spider=None):
        """Initialize Redis connection and determine the dedup key."""
        self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
        # Use the spider name to scope the deduplication set
        spider_name = spider.name if spider else "generic_spider"
        self.redis_key = f"dedup:{spider_name}"
        logger.info(f"DeduplicationPipeline initialized for {spider_name} using key {self.redis_key}")

    def close_spider(self, spider=None):
        """Log final stats and close Redis connection."""
        logger.info(
            f"📊 Deduplication Final stats for {spider.name if spider else 'unknown'}: "
            f"{self.stats['new']} new, {self.stats['duplicates']} duplicates"
        )
        if self.redis_client:
            self.redis_client.close()

    def process_item(self, item, spider=None):
        # 1. Check for required fields
        external_id = item.get('external_id')
        source_domain = item.get('source_domain')
        
        if not external_id or not source_domain:
            logger.warning(f"⚠️ Item missing external_id or source_domain: {item.get('title')}. Skipping dedup check.")
            return item
            
        dedup_key = f"job:{source_domain}:{external_id}"
        
        # 3. Check Redis for duplicates
        if not self.redis_client:
            logger.warning("⚠️ Redis client not initialized. Deduplication check disabled.")
            return item

        try:
            # Check if exists in Redis set
            if self.redis_client.sismember(self.redis_key, dedup_key):
                self.stats['duplicates'] += 1
                logger.info(f"🚫 [DEDUP] Duplicate dropped: {item.get('title')} (ID: {external_id}, Key: {dedup_key})")
                raise DropItem(f"Duplicate item found in {self.redis_key}: {dedup_key}")

            # Add to set and refresh expiry
            self.redis_client.sadd(self.redis_key, dedup_key)
            self.redis_client.expire(self.redis_key, self.ttl_days * 24 * 60 * 60)

            self.stats['new'] += 1
            logger.debug(f"✅ [DEDUP] New item allowed: {item.get('title')} ({external_id})")
        except DropItem:
            raise
        except redis.exceptions.ConnectionError:
            logger.warning("🚫 [DEDUP] Redis connection failed. Skipping deduplication check.")
        except Exception as e:
            logger.error(f"❌ [DEDUP] Deduplication error: {e}")
            
        return item
