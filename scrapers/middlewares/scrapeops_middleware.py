import os
import json
import time
import logging
from urllib.parse import urlencode
from random import randint
import requests

logger = logging.getLogger(__name__)

class ScrapeOpsFakeUserAgentMiddleware:

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def __init__(self, crawler):
        self.crawler = crawler
        settings = crawler.settings
        self.scrapeops_api_key = settings.get('SCRAPEOPS_API_KEY')
        self.scrapeops_endpoint = settings.get('SCRAPEOPS_FAKE_USER_AGENT_ENDPOINT', 'http://headers.scrapeops.io/v1/user-agents?') 
        self.scrapeops_fake_user_agents_active = settings.get('SCRAPEOPS_FAKE_USER_AGENT_ENABLED', False)
        self.scrapeops_num_results = settings.get('SCRAPEOPS_NUM_RESULTS')
        
        self.cache_enabled = settings.get('SCRAPEOPS_CACHE_ENABLED', False)
        self.cache_path = settings.get('SCRAPEOPS_CACHE_PATH')
        self.cache_expiry = settings.get('SCRAPEOPS_CACHE_EXPIRY', 86400)
        
        self.redis_url = settings.get('REDIS_URL')
        self.redis_client = None
        self._init_redis()

        self.user_agents_list = []
        self._load_user_agents()
        self._scrapeops_fake_user_agents_enabled()

    def _init_redis(self):
        if not self.redis_url:
            return
        try:
            import redis
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            logger.info("ScrapeOps Middleware: Redis cache initialized.")
        except Exception as e:
            logger.warning(f"ScrapeOps Middleware: Failed to initialize Redis cache: {e}")

    def _load_user_agents(self):
        """Tries to load user agents from Redis, then File, then API."""
        if not self.cache_enabled:
            self._get_user_agents_from_api()
            return

        # 1. Try Redis
        if self.redis_client:
            try:
                cached_data = self.redis_client.get('scrapeops_user_agents')
                if cached_data:
                    self.user_agents_list = json.loads(cached_data)
                    logger.info(f"ScrapeOps Middleware: Loaded {len(self.user_agents_list)} user agents from Redis.")
                    return
            except Exception as e:
                logger.warning(f"ScrapeOps Middleware: Failed to load from Redis: {e}")

        # 2. Try File Cache
        if self.cache_path and os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, 'r') as f:
                    cache_data = json.load(f)
                    if time.time() - cache_data.get('timestamp', 0) < self.cache_expiry:
                        self.user_agents_list = cache_data.get('result', [])
                        logger.info(f"ScrapeOps Middleware: Loaded {len(self.user_agents_list)} user agents from file cache.")
                        
                        # Sync file cache back to Redis if Redis was empty
                        if self.redis_client and self.user_agents_list:
                            self._save_to_redis(self.user_agents_list)
                        return
                    else:
                        logger.info("ScrapeOps Middleware: File cache expired.")
            except Exception as e:
                logger.warning(f"ScrapeOps Middleware: Failed to load from file cache: {e}")

        # 3. Fallback to API
        self._get_user_agents_from_api()

    def _get_user_agents_from_api(self):
        payload = {'api_key': self.scrapeops_api_key}
        if self.scrapeops_num_results is not None:
            payload['num_results'] = self.scrapeops_num_results
        
        try:
            logger.info("ScrapeOps Middleware: Fetching fresh user agents from API...")
            response = requests.get(self.scrapeops_endpoint, params=urlencode(payload))
            response.raise_for_status()
            json_response = response.json()
            self.user_agents_list = json_response.get('result', [])
            
            if self.user_agents_list and self.cache_enabled:
                self._save_to_cache(self.user_agents_list)
                
        except Exception as e:
            logger.error(f"ScrapeOps Middleware: API call failed: {e}")
            # Keep existing list if any, otherwise empty
            if not self.user_agents_list:
                self.user_agents_list = []

    def _save_to_cache(self, user_agents):
        """Saves user agents to Redis and File."""
        self._save_to_redis(user_agents)
        self._save_to_file(user_agents)

    def _save_to_redis(self, user_agents):
        if self.redis_client:
            try:
                self.redis_client.set('scrapeops_user_agents', json.dumps(user_agents), ex=self.cache_expiry)
                logger.debug("ScrapeOps Middleware: Saved user agents to Redis.")
            except Exception as e:
                logger.warning(f"ScrapeOps Middleware: Failed to save to Redis: {e}")

    def _save_to_file(self, user_agents):
        if self.cache_path:
            try:
                os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)
                cache_data = {
                    'timestamp': time.time(),
                    'result': user_agents
                }
                with open(self.cache_path, 'w') as f:
                    json.dump(cache_data, f)
                logger.debug("ScrapeOps Middleware: Saved user agents to file cache.")
            except Exception as e:
                logger.warning(f"ScrapeOps Middleware: Failed to save to file cache: {e}")

    def _get_random_user_agent(self):
        if not self.user_agents_list:
            return None
        random_index = randint(0, len(self.user_agents_list) - 1)
        return self.user_agents_list[random_index]

    def _scrapeops_fake_user_agents_enabled(self):
        if self.scrapeops_api_key is None or self.scrapeops_api_key == '' or self.scrapeops_fake_user_agents_active == False:
            self.scrapeops_fake_user_agents_active = False
        else:
            self.scrapeops_fake_user_agents_active = True
    
    def process_request(self, request):
        if self.scrapeops_fake_user_agents_active:
            random_user_agent = self._get_random_user_agent()
            if random_user_agent:
                request.headers['User-Agent'] = random_user_agent
                logger.debug(f"ScrapeOps Middleware: Applied User-Agent: {random_user_agent}")
