import sys
import os
import hashlib
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scrapers.pipelines.deduplication_pipeline import DeduplicationPipeline
from scrapy.exceptions import DropItem

def test_deduplication():
    # Mock Redis
    mock_redis = MagicMock()
    # Simulate first time: not a member, second time: is a member
    seen_hashes = set()
    
    def mock_sismember(key, hash_val):
        return hash_val in seen_hashes
        
    def mock_sadd(key, hash_val):
        seen_hashes.add(hash_val)
        return 1
        
    mock_redis.sismember.side_effect = mock_sismember
    mock_redis.sadd.side_effect = mock_sadd
    
    # Initialize pipeline
    pipeline = DeduplicationPipeline(redis_url="redis://localhost:6379")
    pipeline.redis_client = mock_redis
    pipeline.crawler = MagicMock()
    pipeline.crawler.spider.name = "job_leads"
    
    # 1. Test Base Item
    item1 = {
        'source': 'jobleads',
        'external_id': '12345',
        'title': 'Developer',
        'region': 'CA',
        'country_name': 'USA'
    }
    
    print("Processing item 1 (New)...")
    result1 = pipeline.process_item(item1.copy(), None)
    hash1 = result1['dedup_hash']
    print(f"Hash 1: {hash1}")
    
    # 2. Test Exactly Same Item (Should Drop)
    print("\nProcessing item 2 (Duplicate)...")
    try:
        pipeline.process_item(item1.copy(), None)
        print("❌ Error: Duplicate not dropped!")
    except DropItem:
        print("✅ Success: Duplicate dropped as expected.")
        
    # 3. Test Same ID/Title, Different Region (Should be unique)
    item3 = item1.copy()
    item3['region'] = 'NY'
    print("\nProcessing item 3 (Same ID, Different Region)...")
    result3 = pipeline.process_item(item3, None)
    hash3 = result3['dedup_hash']
    print(f"Hash 3: {hash3}")
    if hash1 != hash3:
        print("✅ Success: Different regions produced different hashes.")
    else:
        print("❌ Error: Same hash for different regions!")

    # 4. Test Case Insensitivity
    item4 = item1.copy()
    item4['title'] = 'DEVELOPER'
    print("\nProcessing item 4 (Same metadata, Different Case)...")
    try:
        pipeline.process_item(item4, None)
        print("✅ Success: Title case variation dropped as expected.")
    except DropItem:
        print("✅ Success: Duplicate (case insensitive) dropped.")

if __name__ == "__main__":
    test_deduplication()
