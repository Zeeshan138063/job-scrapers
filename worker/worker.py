import asyncio
import redis.asyncio as redis
import json
import logging
import multiprocessing
import os
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from sqlmodel import Session, create_engine, select
from api.models import SpiderConfig, SpiderRun, JobListing
from prometheus_client import start_http_server, CollectorRegistry, multiprocess
from croniter import croniter
from datetime import datetime

# Database Setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://scraper_user:scraper_pass@db:5432/scraper_staging")
engine = create_engine(DATABASE_URL)

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
    Checks Local Postgres configs and pushes jobs to Redis based on Cron schedule.
    Uses Redis to track last_run times to avoid schema changes.
    """
    def __init__(self, redis_client, engine):
        self.redis_client = redis_client
        self.engine = engine
        self.check_interval = 60 # Check every minute
        
    async def start(self):
        logger.info("Scheduler started (Postgres mode)...")
        while True:
            try:
                await self.check_schedules()
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
            
            await asyncio.sleep(self.check_interval)

    async def check_schedules(self):
        # 1. Fetch active configs from local Postgres
        with Session(self.engine) as session:
            statement = select(SpiderConfig).where(SpiderConfig.is_active == True)
            configs = session.exec(statement).all()
        
        now = datetime.now()
        
        for config_obj in configs:
            config = config_obj.model_dump()
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
            'filters': config.get('filters', {}),
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
        self.running = True
        self.queue_key = 'scraping_queue'
    
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

        # Start Scheduler with local Postgres engine
        scheduler = Scheduler(self.redis_client, engine)
        asyncio.create_task(scheduler.start())

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
            logger.info(f"Received job: {spider_name}")
            
            if not spider_name:
                logger.error("No spider name in job data")
                return

            # Prepare args
            spider_args = {
                'search_queries': job_data.get('search_queries'),
                'locations': job_data.get('locations'),
                'max_pages': job_data.get('max_pages'),
            }
            # Add extra filters
            if 'filters' in job_data and isinstance(job_data['filters'], dict):
                spider_args.update(job_data['filters'])

            # Remove None args
            spider_args = {k: v for k, v in spider_args.items() if v is not None}
            
            # Prepare config overrides
            settings_overrides = {}
            if 'concurrent_requests' in job_data:
                settings_overrides['CONCURRENT_REQUESTS'] = job_data['concurrent_requests']
                
            # Check Local Postgres Config
            try:
                with Session(engine) as session:
                    statement = select(SpiderConfig).where(SpiderConfig.spider_id == spider_name)
                    config = session.exec(statement).first()
                    
                    if config:
                        if not config.is_active:
                            logger.info(f"Skipping {spider_name} - Disabled in configuration")
                            return

                        # Apply DB overrides
                        settings_overrides['CONCURRENT_REQUESTS'] = config.concurrent_requests
                        settings_overrides['DOWNLOAD_DELAY'] = config.download_delay
            except Exception as e:
                logger.error(f"Failed to fetch config from Postgres for {spider_name}: {e}")



            # Run in separate process to allow Reactor restart
            start_time = datetime.now()
            
            # Log RUNNING state in local Postgres
            run_id = None
            try:
                with Session(engine) as session:
                    new_run = SpiderRun(
                        spider_name=spider_name,
                        status='running',
                        created_at=start_time
                    )
                    session.add(new_run)
                    session.commit()
                    session.refresh(new_run)
                    run_id = new_run.id
                    logger.info(f"Started run logging ID: {run_id}")
            except Exception as e:
                logger.error(f"Failed to create run log in Postgres: {e}")

            ctx = multiprocessing.get_context('spawn')
            p = ctx.Process(
                target=run_spider_process,
                args=(spider_name, spider_args, settings_overrides)
            )
            p.start()
            
            # Wait for completion
            while p.is_alive():
                await asyncio.sleep(1)
            p.join()
            
            duration = (datetime.now() - start_time).total_seconds()
            status = 'completed' if p.exitcode == 0 else 'failed'
            
            logger.info(f"Job finished: {spider_name} (Status: {status}, Duration: {duration:.2f}s)")

            # Update run log in local Postgres
            if run_id:
                try:
                    with Session(engine) as session:
                        statement = select(SpiderRun).where(SpiderRun.id == run_id)
                        run_obj = session.exec(statement).one()
                        run_obj.status = status
                        run_obj.duration_seconds = duration
                        run_obj.completed_at = datetime.now()
                        session.add(run_obj)
                        session.commit()
                except Exception as e:
                    logger.error(f"Failed to update run log in Postgres: {e}")

                
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
