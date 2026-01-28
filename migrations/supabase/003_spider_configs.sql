-- 003_spider_configs.sql

CREATE TABLE IF NOT EXISTS scraper_spider_configs (
    spider_id TEXT PRIMARY KEY, -- 'linkedin', 'indeed', etc.
    is_active BOOLEAN DEFAULT TRUE,
    cron_schedule TEXT DEFAULT '0 */4 * * *',
    
    -- Search Parameters
    search_queries TEXT[] DEFAULT ARRAY['python developer'],
    locations TEXT[] DEFAULT ARRAY['Remote'],
    max_pages INTEGER DEFAULT 5,
    
    -- Performance / Scrapy Settings
    concurrent_requests INTEGER DEFAULT 2,
    download_delay NUMERIC(4, 2) DEFAULT 2.0,
    use_crawl4ai BOOLEAN DEFAULT FALSE,
    
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Seed defaults
INSERT INTO scraper_spider_configs (spider_id, is_active, cron_schedule, search_queries, locations, max_pages, concurrent_requests, download_delay, use_crawl4ai)
VALUES 
    ('linkedin_jobs', true, '0 */4 * * *', ARRAY['software engineer'], ARRAY['United States'], 5, 2, 3.0, true),
    ('indeed_jobs', true, '0 */6 * * *', ARRAY['python developer'], ARRAY['Remote'], 10, 5, 1.0, false),
    ('glassdoor_jobs', true, '0 */8 * * *', ARRAY['backend engineer'], ARRAY['San Francisco'], 3, 2, 4.0, true)
ON CONFLICT (spider_id) DO NOTHING;
