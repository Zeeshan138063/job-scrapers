import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlmodel import Session, create_engine, select
from api.models import SpiderConfig

# Database Setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://scraper_user:scraper_pass@localhost:5432/scraper_staging")
engine = create_engine(DATABASE_URL)

def seed_job_leads_config():
    with Session(engine) as session:
        statement = select(SpiderConfig).where(SpiderConfig.spider_id == "job_leads")
        config = session.exec(statement).first()
        
        schedule = os.getenv("JOBLEADS_SCHEDULE", "0 */6 * * *")
        
        if config:
            print(f"Updating existing config for job_leads with schedule: {schedule}")
            config.cron_schedule = schedule
            config.is_active = True
            # Ensure it has some default queries/locations if none exist
            if not config.search_queries:
                config.search_queries = ["Software Engineer", "Developer"]
            if not config.locations:
                config.locations = ["United States", "Germany", "United Kingdom"]
        else:
            print(f"Creating new config for job_leads with schedule: {schedule}")
            config = SpiderConfig(
                spider_id="job_leads",
                is_active=True,
                cron_schedule=schedule,
                search_queries=["Software Engineer", "Developer"],
                locations=["United States", "Germany", "United Kingdom"],
                concurrent_requests=2,
                download_delay=2.0
            )
        
        session.add(config)
        session.commit()
        print("✅ Spider configuration updated successfully.")

if __name__ == "__main__":
    seed_job_leads_config()
