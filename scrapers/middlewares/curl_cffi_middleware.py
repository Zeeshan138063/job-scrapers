import logging

from curl_cffi.requests import AsyncSession
from scrapy import signals
from scrapy.http import HtmlResponse

logger = logging.getLogger(__name__)

class CurlCFFIDownloaderMiddleware:
    """
    Downloader middleware that uses curl_cffi for requests to impersonate browsers.
    Enabled by setting request.meta['use_curl_cffi'] = True.
    
    Supports session isolation via request.meta['curl_cffi_session_id'].
    """

    def __init__(self, crawler, impersonate="chrome124"):
        self.crawler = crawler
        self.impersonate = impersonate
        self.sessions = {}  # session_id -> AsyncSession

    @classmethod
    def from_crawler(cls, crawler):
        impersonate = crawler.settings.get("CURL_CFFI_IMPERSONATE", "chrome124")
        mw = cls(crawler=crawler, impersonate=impersonate)
        crawler.signals.connect(mw.spider_closed, signal=signals.spider_closed)
        return mw

    async def _get_session(self, session_id: str):
        if session_id not in self.sessions:
            logger.debug(f"Creating NEW curl_cffi session for ID: {session_id}")
            self.sessions[session_id] = AsyncSession(impersonate=self.impersonate)
        return self.sessions[session_id]

    async def spider_closed(self, spider):
        # Close all sessions for this spider's name prefix if possible, 
        # but usually we just close everything if the whole spider is closing.
        for sid, session in list(self.sessions.items()):
            await session.close()
            logger.debug(f"Closed curl_cffi session: {sid}")
        self.sessions.clear()

    async def process_request(self, request, spider):
        if not request.meta.get("use_curl_cffi"):
            return None

        # Use explicitly provided session_id or fallback to spider name (shared)
        session_id = request.meta.get("curl_cffi_session_id", spider.name)

        logger.debug(f"Using curl_cffi ({session_id}) for {request.url}")
        session = await self._get_session(session_id)

        method = request.method.upper()
        url = request.url

        # Merge Scrapy headers (decode from bytes)
        headers = {k.decode('utf-8'): v[0].decode('utf-8') for k, v in request.headers.items()}
        
        # Scrapy body is usually bytes
        data = request.body if method in ["POST", "PUT", "PATCH"] else None

        # Handle JSON if specified in Scrapy request
        if request.meta.get("curl_cffi_json"):
            data = request.meta["curl_cffi_json"]

        # Handle initial cookies for a new session
        cookies = request.meta.get("curl_cffi_cookies")

        try:
            resp = await session.request(
                method=method,
                url=url,
                headers=headers,
                data=data,
                cookies=cookies,
                timeout=request.meta.get("download_timeout", 30),
                allow_redirects=request.meta.get("allow_redirects", True),
                proxy=request.meta.get("proxy"),
            )

            # Prepare headers for Scrapy response.
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
            
            return response

        except Exception as e:
            logger.error(f"curl_cffi error for {url}: {e}")
            return None  # Fallback to standard downloader
