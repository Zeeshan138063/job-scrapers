-- 007_add_filters_to_configs.sql
ALTER TABLE scraper_spider_configs ADD COLUMN IF NOT EXISTS filters JSONB DEFAULT '{}';
