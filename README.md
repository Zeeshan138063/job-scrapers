# Job Scraper System

A scalable, distributed job board scraping system built with **Scrapy** and **Crawl4AI**, orchestrating headless browsers to scrape job listings from LinkedIn, Indeed, and Glassdoor.

## 🏗 Architecture

- **Orchestrator**: Scrapy (Python)
- **Rendering Engine**: Crawl4AI (Playwright/Chromium)
- **Queue & Deduplication**: Redis
- **Storage**: Supabase (PostgreSQL)
- **Monitoring**: Prometheus & Grafana
- **Configuration**: Dynamic DB-driven configs + Admin UI

## 🚀 Quick Start

### 1. Prerequisites
- Docker & Docker Compose
- A Supabase project (for database & auth)
- Python 3.11+ (for local development/testing)

### 2. Environment Setup
Create a `.env` file in the `job-scraper` directory:

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:
```ini
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key
REDIS_URL=redis://redis:6379
PROMETHEUS_PORT=9410
LOG_LEVEL=INFO
```

### 3. Database Setup
Run the SQL migrations in your Supabase SQL Editor:
1. `migrations/supabase/001_initial_schema.sql` (Job listings table)
2. `migrations/supabase/002_metrics_schema.sql` (Metrics & Alerts)
3. `migrations/supabase/003_spider_configs.sql` (Dynamic Configs)

### 4. Run with Docker
Start the entire stack (Worker, Redis, Prometheus, Grafana):

```bash
cd docker
docker-compose up --build -d
```

### 5. Trigger a Job
Jobs are triggered by pushing a JSON message to Redis. You can do this via `redis-cli` or a script.

**Example (LinkedIn):**
```bash
docker-compose exec redis redis-cli LPUSH scraping_queue '{"spider": "linkedin_jobs", "search_queries": ["python"], "locations": ["Remote"]}'
```

**Example (Indeed):**
```bash
docker-compose exec redis redis-cli LPUSH scraping_queue '{"spider": "indeed_jobs", "search_queries": ["rust"], "max_pages": 1}'
```

## 📊 Dashboards

### Scraper Admin UI
Manage scraper status, schedules, and concurrency dynamically.
- Open `admin-dashboard/index.html` in your browser.
- Enter your Supabase URL & Key.

### Grafana (Monitoring)
View real-time metrics (Items scraped, Error rates, Latency).
- URL: `http://localhost:3000`
- Login: `admin` / `admin` (default)
- **Setup**:
    1. Go to **Configuration** > **Data Sources** > **Add data source**.
    2. Select **Prometheus**.
    3. URL: `http://prometheus:9090`.
    4. Save & Test.
    5. Import dashboard from `grafana/dashboards/scraper_overview.json`.

## 🛠 Local Development
To run scrapers locally without Docker:

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

2. Run the worker:
   ```bash
   python worker/worker.py
   ```

3. Run tests:
   ```bash
   scripts/test_runner.sh
   ```
