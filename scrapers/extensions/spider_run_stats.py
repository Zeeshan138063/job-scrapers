import os
import time
from datetime import datetime, timezone
import logging
from typing import Optional

from scrapy import signals
from sqlmodel import Session, create_engine, select
from scrapers.models import SpiderRun

logger = logging.getLogger(__name__)

class SpiderRunStatsExtension:
    """
    Scrapy extension that records spider run metadata to the database.
    Tracks start time, end time, items scraped, and errors.
    """

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = create_engine(self.database_url)
        self.run_id: Optional[int] = None
        self.start_time: float = 0

    @classmethod
    def from_crawler(cls, crawler):
        db_url = crawler.settings.get('DATABASE_URL')
        if not db_url:
            logger.error("SpiderRunStatsExtension: DATABASE_URL not set in settings.")
            raise ValueError("DATABASE_URL must be set")

        ext = cls(db_url)
        crawler.signals.connect(ext.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(ext.spider_closed, signal=signals.spider_closed)
        return ext

    def spider_opened(self, spider):
        self.start_time = time.time()
        logger.info(f"📊 Stats Extension: Creating run record for {spider.name}")
        
        try:
            with Session(self.engine) as session:
                run = SpiderRun(
                    spider_name=spider.name,
                    status="running",
                    created_at=datetime.now(timezone.utc)
                )
                session.add(run)
                session.commit()
                session.refresh(run)
                self.run_id = run.id
        except Exception as e:
            logger.error(f"📊 Stats Extension: Failed to create run record: {e}")

    def _humanize_duration(self, seconds: float) -> str:
        """Converts seconds to human-readable format like '1h 2m 3s'."""
        if seconds < 60:
            return f"{seconds:.1f}s"
        m, s = divmod(int(seconds), 60)
        h, m = divmod(m, 60)
        if h > 0:
            return f"{h}h {m}m {s}s"
        return f"{m}m {s}s"

    def spider_closed(self, spider, reason):
        if self.run_id is None:
            return

        duration = time.time() - self.start_time
        human_dur = self._humanize_duration(duration)
        
        stats = spider.crawler.stats.get_stats()
        items_scraped = stats.get('item_scraped_count', 0)
        errors_count = stats.get('log_count/ERROR', 0)
        
        logger.info(f"📊 Stats Extension: Updating run {self.run_id} ({human_dur}, {items_scraped} items)")

        try:
            with Session(self.engine) as session:
                run = session.get(SpiderRun, self.run_id)
                if run:
                    run.status = "completed" if reason == "finished" else f"stopped ({reason})"
                    run.duration_seconds = duration
                    run.human_duration = human_dur
                    run.completed_at = datetime.now(timezone.utc)
                    run.items_scraped = items_scraped
                    run.errors_count = errors_count
                    run.metadata_json = {
                        "reason": reason,
                        "finish_stats": {
                            k: v for k, v in stats.items() 
                            if isinstance(v, (int, float, str, bool))
                        }
                    }
                    session.add(run)
                    session.commit()
        except Exception as e:
            logger.error(f"📊 Stats Extension: Failed to update run record: {e}")
