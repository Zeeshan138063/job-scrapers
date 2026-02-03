from scrapy.exceptions import DropItem
import logging

logger = logging.getLogger(__name__)


class ValidationPipeline:
    """
    Pipeline 1: Validate items before processing
    Fail-fast pattern
    """
    
    REQUIRED_FIELDS = ['title', 'company', 'url', 'source']
    
    def process_item(self, item):
        """Validate required fields and clean data"""
        
        # Check required fields
        missing = [field for field in self.REQUIRED_FIELDS if not item.get(field)]
        
        if missing:
            raise DropItem(f"Missing required fields: {missing} in {item.get('url', 'unknown')}")
        
        # Clean whitespace from string fields
        for field in item:
            if isinstance(item[field], str):
                item[field] = item[field].strip()
        
        # Validate URL format
        if not item['url'].startswith('http'):
            raise DropItem(f"Invalid URL format: {item['url']}")
        
        # Ensure external_id exists (fallback to hash of URL)
        if not item.get('external_id'):
            import hashlib
            item['external_id'] = hashlib.md5(item['url'].encode()).hexdigest()[:16]
        
        logger.debug(f"Validated: {item['title']} at {item['company']}")
        
        return item
