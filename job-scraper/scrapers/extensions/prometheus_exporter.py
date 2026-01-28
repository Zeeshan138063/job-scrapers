from prometheus_client import Counter, Gauge, Histogram, start_http_server
from scrapy import signals
from scrapy.exceptions import NotConfigured
import time
import logging

logger = logging.getLogger(__name__)


class PrometheusStatsExtension:
    """
    Exports Scrapy metrics in Prometheus format
    Exposes /metrics endpoint on configured port
    """
    
    def __init__(self, port=9410):
        self.port = port
        
        # Counters
        self.items_scraped_total = Counter(
            'scrapy_items_scraped_total',
            'Total number of items scraped',
            ['spider', 'source']
        )
        
        self.items_dropped_total = Counter(
            'scrapy_items_dropped_total',
            'Total number of items dropped',
            ['spider', 'reason']
        )
        
        self.requests_total = Counter(
            'scrapy_requests_total',
            'Total number of requests made',
            ['spider', 'method']
        )
        
        self.responses_total = Counter(
            'scrapy_responses_total',
            'Total number of responses received',
            ['spider', 'status_code']
        )
        
        self.errors_total = Counter(
            'scrapy_errors_total',
            'Total number of errors',
            ['spider', 'error_type']
        )
        
        # Gauges
        self.spider_status = Gauge(
            'scrapy_spider_status',
            'Spider status (1=running, 0=stopped)',
            ['spider']
        )
        
        self.active_requests = Gauge(
            'scrapy_active_requests',
            'Number of active requests',
            ['spider']
        )
        
        # Histograms
        self.response_time_seconds = Histogram(
            'scrapy_response_time_seconds',
            'Response time in seconds',
            ['spider'],
            buckets=(0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30)
        )
        
        self.item_processing_time_seconds = Histogram(
            'scrapy_item_processing_time_seconds',
            'Time to process an item',
            ['spider'],
            buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1)
        )
        
        self.request_start_times = {}
    
    @classmethod
    def from_crawler(cls, crawler):
        if not crawler.settings.getbool('PROMETHEUS_ENABLED', True):
            raise NotConfigured
        
        port = crawler.settings.getint('PROMETHEUS_PORT', 9410)
        ext = cls(port=port)
        
        crawler.signals.connect(ext.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(ext.spider_closed, signal=signals.spider_closed)
        crawler.signals.connect(ext.item_scraped, signal=signals.item_scraped)
        crawler.signals.connect(ext.item_dropped, signal=signals.item_dropped)
        crawler.signals.connect(ext.request_scheduled, signal=signals.request_scheduled)
        crawler.signals.connect(ext.response_received, signal=signals.response_received)
        crawler.signals.connect(ext.spider_error, signal=signals.spider_error)
        
        return ext
    
    
    def spider_opened(self, spider):
        logger.info(f"Prometheus exporter initialized for {spider.name}")
        self.spider_status.labels(spider=spider.name).set(1)
    
    def spider_closed(self, spider):
        self.spider_status.labels(spider=spider.name).set(0)
        self.active_requests.labels(spider=spider.name).set(0)
    
    def item_scraped(self, item, response, spider):
        source = item.get('source', 'unknown')
        self.items_scraped_total.labels(spider=spider.name, source=source).inc()
        
        if hasattr(item, '_processing_start_time'):
            processing_time = time.time() - item['_processing_start_time']
            self.item_processing_time_seconds.labels(spider=spider.name).observe(processing_time)
    
    def item_dropped(self, item, response, exception, spider):
        reason = exception.__class__.__name__ if exception else 'Unknown'
        self.items_dropped_total.labels(spider=spider.name, reason=reason).inc()
    
    def request_scheduled(self, request, spider):
        self.requests_total.labels(spider=spider.name, method=request.method).inc()
        self.active_requests.labels(spider=spider.name).inc()
        self.request_start_times[id(request)] = time.time()
    
    def response_received(self, response, request, spider):
        self.responses_total.labels(spider=spider.name, status_code=response.status).inc()
        self.active_requests.labels(spider=spider.name).dec()
        
        request_id = id(request)
        if request_id in self.request_start_times:
            latency = time.time() - self.request_start_times[request_id]
            self.response_time_seconds.labels(spider=spider.name).observe(latency)
            del self.request_start_times[request_id]
    
    def spider_error(self, failure, response, spider):
        error_type = failure.type.__name__ if hasattr(failure, 'type') else 'Unknown'
        self.errors_total.labels(spider=spider.name, error_type=error_type).inc()
