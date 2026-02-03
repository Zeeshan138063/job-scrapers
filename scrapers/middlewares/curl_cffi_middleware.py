import logging
import asyncio
from curl_cffi.requests import AsyncSession
from scrapy import signals
from scrapy.http import HtmlResponse, Response
from scrapy.utils.python import to_bytes

logger = logging.getLogger(__name__)

class CurlCFFIDownloaderMiddleware:
    """
    Downloader middleware that uses curl_cffi for requests to impersonate browsers.
    Enabled by setting request.meta['use_curl_cffi'] = True.
    """

    def __init__(self, crawler, impersonate="chrome124"):
        self.crawler = crawler
        self.impersonate = impersonate
        self.sessions = {}  # spider_name -> AsyncSession

    @classmethod
    def from_crawler(cls, crawler):
        impersonate = crawler.settings.get("CURL_CFFI_IMPERSONATE", "chrome124")
        mw = cls(crawler=crawler, impersonate=impersonate)
        crawler.signals.connect(mw.spider_closed, signal=signals.spider_closed)
        return mw

    def _get_spider_name(self):
        return self.crawler.spider.name if self.crawler.spider else "default"

    async def _get_session(self):
        spider_name = self._get_spider_name()
        if spider_name not in self.sessions:
            self.sessions[spider_name] = AsyncSession(impersonate=self.impersonate)
        return self.sessions[spider_name]

    async def spider_closed(self):
        spider_name = self._get_spider_name()
        session = self.sessions.pop(spider_name, None)
        if session:
            await session.close()
            logger.debug(f"Closed curl_cffi session for {spider_name}")

    async def process_request(self, request):
        if not request.meta.get("use_curl_cffi"):
            return None

        logger.debug(f"Using curl_cffi for {request.url}")
        session = await self._get_session()

        method = request.method.upper()
        url = request.url
        headers = {k.decode('utf-8'): v[0].decode('utf-8') for k, v in request.headers.items()}
        
        # Scrapy body is usually bytes
        data = request.body if method in ["POST", "PUT", "PATCH"] else None
        
        # Handle JSON if specified in Scrapy request (common in our case)
        if request.meta.get("curl_cffi_json"):
            data = request.meta["curl_cffi_json"]

        try:
            resp = await session.request(
                method=method,
                url=url,
                headers=headers,
                data=data,
                timeout=request.meta.get("download_timeout", 30),
                allow_redirects=request.meta.get("allow_redirects", True),
                proxy=request.meta.get("proxy"),
            )

            # Prepare headers for Scrapy response.
            # We must handle multiple 'Set-Cookie' headers correctly.
            scrapy_headers = {}
            for k, v in resp.headers.multi_items():
                if k.lower() in ['content-encoding', 'content-length']:
                    continue
                if k not in scrapy_headers:
                    scrapy_headers[k] = []
                scrapy_headers[k].append(v)

            # Convert curl_cffi response to Scrapy response
            response = HtmlResponse(
                url=str(resp.url),
                status=resp.status_code,
                headers=scrapy_headers,
                body=resp.content,
                encoding=resp.encoding or 'utf-8',
                request=request,
            )
            
            # Sync cookies back to the spider if needed
            # (Though AsyncSession handles them internally if reused)
            
            return response

        except Exception as e:
            logger.error(f"curl_cffi error for {url}: {e}")
            return None # Fallback to standard downloader or let Scrapy handle error
