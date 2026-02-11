import os
from sqlmodel import Session, create_engine, select
from api.models import SpiderConfig, SQLModel

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://scraper_user:scraper_pass@localhost:5432/scraper_staging")
engine = create_engine(DATABASE_URL)

def seed_configs():
    SQLModel.metadata.create_all(engine)
    
    with Session(engine) as session:
        # Check if already seeded
        existing = session.exec(select(SpiderConfig)).first()
        if existing:
            print("Database already contains configurations. Skipping seed.")
            return

        print("Seeding default configurations...")
        configs = [
            SpiderConfig(
                spider_id="job_leads_v2",
                search_queries=["fullstack dev", "python developer"],
                locations=["NLD", "DEU"],
                cron_schedule="0 */6 * * *",
                concurrent_requests=2,
                download_delay=3.0,
                filters={"min_salary": 40000, "radius": 50}
            ),
            SpiderConfig(
                spider_id="linkedin_jobs",
                search_queries=["software engineer"],
                locations=["United States"],
                cron_schedule="0 */4 * * *",
                concurrent_requests=1,
                download_delay=5.0,
                use_crawl4ai=True
            ),
            SpiderConfig(
                spider_id="indeed_jobs",
                search_queries=["python developer"],
                locations=["Remote"],
                cron_schedule="0 */8 * * *",
                concurrent_requests=5,
                download_delay=1.0
            )
        ]
        
        for c in configs:
            session.add(c)
        
        session.commit()
        print("Seeding completed successfully.")

if __name__ == "__main__":
    seed_configs()
