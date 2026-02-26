
import os
import sys
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scrapers.spiders.job_leads import JobLeadsSpider

def run_debug_spider():
    settings = get_project_settings()
    # Ensure logs are visible
    settings.set('LOG_LEVEL', 'DEBUG')
    # Run only for 1 item
    process = CrawlerProcess(settings)
    process.crawl(JobLeadsSpider, country="USA", limit=1)
    process.start()

if __name__ == "__main__":
    # Add project root to sys.path
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    sys.path.insert(0, project_root)
    run_debug_spider()
