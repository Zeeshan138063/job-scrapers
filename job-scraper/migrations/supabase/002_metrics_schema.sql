-- 002_metrics_schema.sql

-- Scraper runs table
CREATE TABLE IF NOT EXISTS scraper_runs (
    id BIGSERIAL PRIMARY KEY,
    spider_name TEXT NOT NULL,
    status TEXT NOT NULL, -- 'completed', 'failed'
    duration_seconds NUMERIC(10, 2),
    items_scraped INTEGER DEFAULT 0,
    items_dropped INTEGER DEFAULT 0,
    success_rate NUMERIC(5, 2),
    error_count INTEGER DEFAULT 0,
    errors JSONB,
    completed_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for fast queries
CREATE INDEX idx_scraper_runs_spider_name ON scraper_runs(spider_name);
CREATE INDEX idx_scraper_runs_completed_at ON scraper_runs(completed_at DESC);
CREATE INDEX idx_scraper_runs_status ON scraper_runs(status);

-- Alerts table
CREATE TABLE IF NOT EXISTS scraper_alerts (
    id BIGSERIAL PRIMARY KEY,
    spider_name TEXT NOT NULL,
    severity TEXT NOT NULL, -- 'info', 'warning', 'error'
    message TEXT NOT NULL,
    metadata JSONB,
    resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_scraper_alerts_unresolved ON scraper_alerts(created_at DESC) 
WHERE resolved = FALSE;

-- Aggregate metrics view (for dashboard)
CREATE OR REPLACE VIEW scraper_health_summary AS
SELECT 
    spider_name,
    COUNT(*) as total_runs,
    COUNT(*) FILTER (WHERE status = 'completed') as successful_runs,
    COUNT(*) FILTER (WHERE status = 'failed') as failed_runs,
    ROUND(AVG(success_rate), 2) as avg_success_rate,
    ROUND(AVG(duration_seconds), 2) as avg_duration,
    ROUND(AVG(items_scraped), 0) as avg_items_scraped,
    MAX(completed_at) as last_run_at,
    SUM(items_scraped) as total_items_scraped
FROM scraper_runs
WHERE completed_at > NOW() - INTERVAL '7 days'
GROUP BY spider_name;
