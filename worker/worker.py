import asyncio
import redis.asyncio as redis
import json
import logging
import multiprocessing
import os
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from supabase import create_client
from scrapy.utils.project import get_project_settings
from supabase import create_client
from scrapy.utils.project import get_project_settings
from supabase import create_client
from prometheus_client import start_http_server, CollectorRegistry, multiprocess
from croniter import croniter
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

def run_spider_process(spider_name: str, spider_args: dict, settings_overrides: dict):
    """
    Function to run in a separate process.
    Initializes a new Reactor and CrawlerProcess for each job.
    """
    try:
        # Get project settings
        settings = get_project_settings()
        
        # Apply overrides
        for key, value in settings_overrides.items():
            settings.set(key, value)
            
        # Create crawler process
        process = CrawlerProcess(settings)
        
        # Start crawling
        process.crawl(spider_name, **spider_args)
        process.start() # Blocks until finished
        
    except Exception as e:
        logger.error(f"Process error running {spider_name}: {e}")
        # We don't re-raise here to avoid crashing the worker, 
        # but in a real system we might want to exit with non-zero code.
class Scheduler:
    """
    Checks Supabase configs and pushes jobs to Redis based on Cron schedule.
    Uses Redis to track last_run times to avoid schema changes.
    """
    def __init__(self, redis_client, supabase_url, supabase_key):
        self.redis_client = redis_client
        self.supabase = create_client(supabase_url, supabase_key)
        self.check_interval = 60 # Check every minute
        
    async def start(self):
        logger.info("Scheduler started...")
        while True:
            try:
                await self.check_schedules()
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
            
            await asyncio.sleep(self.check_interval)

    async def check_schedules(self):
        # 1. Fetch active configs
        res = self.supabase.table('scraper_spider_configs').select('*').eq('is_active', True).execute()
        configs = res.data or []
        
        now = datetime.now()
        
        for config in configs:
            spider_id = config['spider_id']
            cron_schedule = config.get('cron_schedule')
            
            if not cron_schedule:
                continue

            # 2. Check last run time from Redis
            last_run_key = f"scheduler:last_run:{spider_id}"
            last_run_ts = await self.redis_client.get(last_run_key)
            
            should_run = False
            
            if not last_run_ts:
                # First time seeing this? Let's assume we run it if it matches NOW
                # Or safely, wait for next occurrence. 
                # Let's say we set last_run to now, effectively skipping the immediate trigger 
                # unless we want "Run on Startup" logic.
                # User wants "schedule a job on scraper it should act".
                # Let's verify if current time matches cron.
                if croniter.match(cron_schedule, now):
                    should_run = True
                else:
                    # just mark seen
                    pass
            else:
                # Check if we passed a schedule point since last run
                # croniter get_next from last_run
                last_run_dt = datetime.fromtimestamp(float(last_run_ts))
                iter = croniter(cron_schedule, last_run_dt)
                next_run = iter.get_next(datetime)
                
                if next_run <= now:
                    should_run = True
            
            if should_run:
                await self.schedule_job(config)
                # Update last run to now
                await self.redis_client.set(last_run_key, now.timestamp())

    async def schedule_job(self, config):
        spider_id = config['spider_id']
        logger.info(f"⏰ Scheduling job for {spider_id}")
        
        job_data = {
            'spider': spider_id,
            'search_queries': config.get('search_queries'),
            'locations': config.get('locations'),
            'max_pages': config.get('max_pages'),
            'concurrent_requests': config.get('concurrent_requests'),
            'created_at': datetime.now().isoformat()
        }
        
        # Push to Redis Queue
        await self.redis_client.rpush('scraping_queue', json.dumps(job_data))

class ScrapingWorker:
    """
    Worker that processes scraping jobs from Redis queue
    """
    
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.redis_client = None
        self.redis_client = None
        self.running = True
        self.queue_key = 'scraping_queue'
        
        # Initialize Supabase client for logging
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        if supabase_url and supabase_key:
            self.supabase = create_client(supabase_url, supabase_key)
        else:
            self.supabase = None
            logger.warning("Supabase credentials missing. Run logging disabled.")
    
    async def connect(self):
        self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
        logger.info(f"Connected to Redis at {self.redis_url}")
    
    async def run(self):
        await self.connect()
        
        # Start Prometheus Metrics Server (Multiprocess Mode)
        if 'PROMETHEUS_MULTIPROC_DIR' in os.environ:
            registry = CollectorRegistry()
            multiprocess.MultiProcessCollector(registry)
            start_http_server(9410, registry=registry)
            logger.info("Prometheus metrics server started on port 9410")
        else:
            logger.warning("PROMETHEUS_MULTIPROC_DIR not set. Metrics will not be aggregated.")



        # Start Scheduler (if configured)
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        if supabase_url and supabase_key:
            scheduler = Scheduler(self.redis_client, supabase_url, supabase_key)
            asyncio.create_task(scheduler.start())
        else:
            logger.warning("Supabase credentials missing. Scheduler disabled.")

        logger.info(f"Worker started, listening on {self.queue_key}...")
        
        while self.running:
            try:
                # BLPOP returns (key, value) or None
                result = await self.redis_client.blpop(self.queue_key, timeout=5)
                
                if result:
                    _, job_json = result
                    await self.process_job(job_json)
                    
            except Exception as e:
                logger.error(f"Worker loop error: {e}")
                await asyncio.sleep(5)
                
    async def process_job(self, job_json: str):
        try:
            job_data = json.loads(job_json)
            spider_name = job_data.get('spider')
            logger.info(f"d Received job: {spider_name}")
            
            if not spider_name:
                logger.error("No spider name in job data")
                return

            # Prepare args
            spider_args = {
                'search_queries': job_data.get('search_queries'),
                'locations': job_data.get('locations'),
                'max_pages': job_data.get('max_pages'),
            }
            # Remove None args
            spider_args = {k: v for k, v in spider_args.items() if v is not None}
            
            # Prepare config overrides
            settings_overrides = {}
            if 'concurrent_requests' in job_data:
                settings_overrides['CONCURRENT_REQUESTS'] = job_data['concurrent_requests']
                
            # Check Supabase Config
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_KEY')
            if supabase_url and supabase_key:
                try:
                    client = create_client(supabase_url, supabase_key)
                    res = client.table('scraper_spider_configs').select('*').eq('spider_id', spider_name).execute()
                    if res.data:
                        config = res.data[0]
                        if not config.get('is_active', True):
                            logger.info(f"Skipping {spider_name} - Disabled in configuration")
                            return

                        # Apply DB Concurrency overrides
                        if 'concurrent_requests' in config:
                            settings_overrides['CONCURRENT_REQUESTS'] = config['concurrent_requests']
                        if 'download_delay' in config:
                            settings_overrides['DOWNLOAD_DELAY'] = config['download_delay']
                except Exception as e:
                    logger.error(f"Failed to fetch config for {spider_name}: {e}")



            # Run in separate process to allow Reactor restart
            start_time = datetime.now()
            
            # Log RUNNING state
            run_id = None
            if self.supabase:
                try:
                    res = self.supabase.table('scraper_runs').insert({
                        'spider_name': spider_name,
                        'status': 'running',
                        'created_at': start_time.isoformat()
                    }).execute()
                    if res.data:
                        run_id = res.data[0]['id']
                        logger.info(f"Started run logging ID: {run_id}")
                except Exception as e:
                    logger.error(f"Failed to create run log: {e}")

            ctx = multiprocessing.get_context('spawn')
            p = ctx.Process(
                target=run_spider_process,
                args=(spider_name, spider_args, settings_overrides)
            )
            p.start()
            
            # Wait for completion (or run async if parallel jobs desired)
            # For now, we process 1 job at a time per worker instance
            while p.is_alive():
                await asyncio.sleep(1)
            p.join()
            
            duration = (datetime.now() - start_time).total_seconds()
            status = 'completed' if p.exitcode == 0 else 'failed'
            
            logger.info(f"Job finished: {spider_name} (Status: {status}, Duration: {duration:.2f}s)")

            # Update run log
            if self.supabase and run_id:
                try:
                    self.supabase.table('scraper_runs').update({
                        'status': status,
                        'duration_seconds': duration,
                        'completed_at': datetime.now().isoformat(),
                        # For now we don't have exact items stats from the process easily 
                        # without sharing memory or parsing logs. 
                        # We can implement a Redis-based stats collector later.
                    }).eq('id', run_id).execute()
                    
                    # ALSO: If failed, create an alert
                    if status == 'failed':
                        self.supabase.table('scraper_alerts').insert({
                            'spider_name': spider_name,
                            'severity': 'error',
                            'message': f"Job failed with exit code {p.exitcode}",
                            'metadata': {'run_id': run_id, 'duration': duration}
                        }).execute()
                        
                except Exception as e:
                    logger.error(f"Failed to update run log: {e}")
                
        except json.JSONDecodeError:
            logger.error("Failed to decode job JSON")
        except Exception as e:
            logger.error(f"Error processing job: {e}")

if __name__ == "__main__":
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
    worker = ScrapingWorker(redis_url)
    
    try:
        asyncio.run(worker.run())
    except KeyboardInterrupt:
        logger.info("Worker stopping...")
