import json
import logging
import aiohttp
from scrapy import signals
from scrapy.http import HtmlResponse

logger = logging.getLogger(__name__)


class Crawl4AIDownloaderMiddleware:
    """
    Adapter Pattern (Remote): Sends requests to external Crawl4AI service
    """
    
    def __init__(self, api_url, api_token=None):
        self.api_url = api_url
        self.api_token = api_token
        self.stats = {'requests': 0, 'successes': 0, 'failures': 0}
    
    @classmethod
    def from_crawler(cls, crawler):
        # Default to localhost if not set, or user provided URL
        # We append /crawl if the user gave the root URL, unless they specified the full endpoint
        base_url = crawler.settings.get('CRAWL4AI_API_URL', 'http://localhost:8000')
        if not base_url.endswith('/crawl'):
             # Heuristic: if it ends in slash, likely root.
             # User gave https://scrapping.zeeshare.com/playground/
             # API is likely https://scrapping.zeeshare.com/crawl or similar. 
             # I will assume standard /crawl endpoint for now.
             base_url = base_url.rstrip('/') + '/crawl'

        return cls(
            api_url=base_url,
            api_token=crawler.settings.get('CRAWL4AI_API_TOKEN')
        )

    def process_request(self, request, spider):
        # Only process if explicitly marked
        if not request.meta.get('use_crawl4ai', False):
            return None
            
        # Scrapy is async, so we return a Deferred/Future. 
        # But process_request expects Response or Request or None.
        # To do async I/O in middleware, we should return a Deferred.
        # Scrapy supports async def since 2.0.
        return self._process_async(request, spider)

    async def _process_async(self, request, spider):
        self.stats['requests'] += 1
        logger.debug(f"Calling Remote Crawl4AI for: {request.url}")
        
        # Prepare payload
        payload = {
            "urls": request.url, # API usually takes string or list
            "priority": 10,
        }
        
        # Add optional params from meta
        if request.meta.get('wait_for'):
            payload['wait_for'] = request.meta['wait_for']
        if request.meta.get('css_selector'):
            payload['css_selector'] = request.meta['css_selector']
        if request.meta.get('js_code'):
            payload['js_code'] = request.meta['js_code']
            
        headers = {'Content-Type': 'application/json'}
        if self.api_token:
            headers['Authorization'] = f"Bearer {self.api_token}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Assuming API returns { results: [ { html: "...", ... } ] } or similar
                        # or just the result object.
                        # I'll try to handle common response formats.
                        
                        html_content = ""
                        if 'results' in data and isinstance(data['results'], list):
                             html_content = data['results'][0].get('html', '')
                        elif 'html' in data:
                             html_content = data['html']
                        else:
                             # Fallback check
                             html_content = str(data)

                        self.stats['successes'] += 1
                        return HtmlResponse(
                            url=request.url,
                            body=html_content.encode('utf-8'),
                            encoding='utf-8',
                            request=request,
                            status=200
                        )
                    else:
                        error_text = await response.text()
                        logger.error(f"Crawl4AI Remote Error: Status={response.status}, Body={error_text}")
                        self.stats['failures'] += 1
                        
                        # Return a 200 response with error info so Scrapy doesn't ignore it immediately, 
                        # allowing us to see the error in the spider if needed, OR just let it drop.
                        # For now, let's return it as 500 so we see it in stats.
                        return HtmlResponse(
                            url=request.url,
                            status=500, # Force 500 to indicate failure to Scrapy
                            request=request,
                            body=f"Crawl4AI Error: {error_text}".encode('utf-8')
                        )
                        
        except Exception as e:
            logger.error(f"Failed to connect to Crawl4AI API: {e}")
            self.stats['failures'] += 1
            return None

