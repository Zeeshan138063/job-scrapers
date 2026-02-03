import os

# Scrapy settings for job_scraper project
BOT_NAME = 'job_scraper'

SPIDER_MODULES = ['scrapers.spiders']
NEWSPIDER_MODULE = 'scrapers.spiders'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests
CONCURRENT_REQUESTS = 16
CONCURRENT_REQUESTS_PER_DOMAIN = 4

# Configure download delay
DOWNLOAD_DELAY = 2
RANDOMIZE_DOWNLOAD_DELAY = True

# Disable cookies (enabled by default)
COOKIES_ENABLED = True

# Disable Telnet Console (enabled by default)
TELNETCONSOLE_ENABLED = False

# Override the default request headers
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en',
}

# Enable or disable downloader middlewares
DOWNLOADER_MIDDLEWARES = {
    'scrapers.middlewares.scrapeops_middleware.ScrapeOpsFakeUserAgentMiddleware': 400,
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    'scrapers.middlewares.curl_cffi_middleware.CurlCFFIDownloaderMiddleware': 580,
    'scrapers.middlewares.crawl4ai_middleware.Crawl4AIDownloaderMiddleware': 585,
}

# Enable or disable extensions
EXTENSIONS = {
    'scrapers.extensions.prometheus_exporter.PrometheusStatsExtension': 500,
}

# Configure item pipelines (order matters!)
ITEM_PIPELINES = {
    'scrapers.pipelines.validation_pipeline.ValidationPipeline': 100,
    'scrapers.pipelines.deduplication_pipeline.DeduplicationPipeline': 200,
    'scrapers.pipelines.enrichment_pipeline.EnrichmentPipeline': 300,
    'scrapers.pipelines.supabase_pipeline.SupabasePipeline': 400,
}

# Enable AutoThrottle extension
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0
AUTOTHROTTLE_DEBUG = False

# Enable showing throttling stats
STATS_CLASS = 'scrapy.statscollectors.MemoryStatsCollector'

# User agent
# USER_AGENT = 'JobScraperBot/1.0 (+https://yoursite.com/bot)'

# Retry settings
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 429]

# Logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s [%(name)s] %(levelname)s: %(message)s'
LOG_DATEFORMAT = '%Y-%m-%d %H:%M:%S'

# Environment variables
REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379')
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# Prometheus settings
PROMETHEUS_ENABLED = True
PROMETHEUS_PORT = int(os.getenv('PROMETHEUS_PORT', 9410))

# Deduplication settings
DEDUP_TTL_DAYS = int(os.getenv('DEDUP_TTL_DAYS', 30))

# Remote Crawl4AI Settings
CRAWL4AI_API_URL = os.getenv('CRAWL4AI_API_URL', 'https://scrapping.zeeshare.com')
CRAWL4AI_API_TOKEN = os.getenv('CRAWL4AI_API_TOKEN')

# Spider configuration path
SPIDER_CONFIG_PATH = os.getenv('SPIDER_CONFIG_PATH', '/app/config/spiders.yml')

CURL_CFFI_IMPERSONATE = os.getenv('CURL_CFFI_IMPERSONATE', 'chrome124')

# ScrapeOps Fake User-Agent Settings
SCRAPEOPS_API_KEY = 'dc6c5839-c058-4683-b1a2-cf23693d733b'
SCRAPEOPS_FAKE_USER_AGENT_ENABLED = True
SCRAPEOPS_CACHE_ENABLED = True
SCRAPEOPS_CACHE_PATH = os.path.join(os.path.dirname(__file__), 'data', 'scrapeops_ua_cache.json')
SCRAPEOPS_CACHE_EXPIRY = 86400  # 24 hours