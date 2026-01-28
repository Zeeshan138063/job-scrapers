-- 005_allow_running_state.sql
ALTER TABLE scraper_runs ALTER COLUMN completed_at DROP NOT NULL;
