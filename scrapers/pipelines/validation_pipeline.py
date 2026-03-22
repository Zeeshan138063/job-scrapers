import logging

from scrapy.exceptions import DropItem

logger = logging.getLogger(__name__)


class ValidationPipeline:
    """
    Pipeline 1: Validate items before processing
    Fail-fast pattern
    """
    
    REQUIRED_FIELDS = ['title', 'url', 'source']
    
    def process_item(self, item, spider=None):
        """Validate required fields and clean data"""
        
        # Check required fields
        missing = [field for field in self.REQUIRED_FIELDS if not item.get(field)]
        
        # Special check for company/company_name
        if not item.get('company') and not item.get('company_name'):
            missing.append('company/company_name')
        
        if missing:
            msg = f"🚫 [VALIDATION] Missing required fields: {missing} in {item.get('title', 'unknown')}"
            logger.info(msg)
            raise DropItem(msg)
        
        # Clean whitespace from string fields
        for field in item:
            if isinstance(item[field], str):
                item[field] = item[field].strip()
        
        # Validate URL format
        if not item['url'].startswith('http'):
            msg = f"🚫 [VALIDATION] Invalid URL format for {item.get('title')}: {item['url']}"
            logger.info(msg)
            raise DropItem(msg)
        
        # Ensure external_id exists (fallback to hash of URL)
        if not item.get('external_id'):
            import hashlib
            item['external_id'] = hashlib.md5(item['url'].encode()).hexdigest()[:16]
        
        logger.debug(f"Validated: {item['title']} at {item['company']}")
        
        return item
