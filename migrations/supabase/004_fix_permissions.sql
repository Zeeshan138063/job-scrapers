-- 004_fix_permissions.sql

-- Enable RLS but allow access for now (since we use anon/authenticated keys)
ALTER TABLE scraper_spider_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE scraper_job_listings ENABLE ROW LEVEL SECURITY;

-- Allow read access to everyone (or just authenticated if you prefer)
-- For this internal scraper dashboard, we'll open it up to the API key holders.

CREATE POLICY "Enable read access for all users" ON scraper_spider_configs
    FOR SELECT USING (true);

CREATE POLICY "Enable update access for all users" ON scraper_spider_configs
    FOR UPDATE USING (true);

CREATE POLICY "Enable insert access for all users" ON scraper_spider_configs
    FOR INSERT WITH CHECK (true);

-- Re-seed if empty
INSERT INTO scraper_spider_configs (spider_id, is_active, cron_schedule, search_queries, locations, max_pages, concurrent_requests, download_delay, use_crawl4ai)
VALUES 
    ('linkedin_jobs', true, '0 */4 * * *', ARRAY['software engineer'], ARRAY['United States'], 5, 2, 3.0, true),
    ('indeed_jobs', true, '0 */6 * * *', ARRAY['python developer'], ARRAY['Remote'], 10, 5, 1.0, false),
    ('glassdoor_jobs', true, '0 */8 * * *', ARRAY['backend engineer'], ARRAY['San Francisco'], 3, 2, 4.0, true)
ON CONFLICT (spider_id) DO NOTHING;
