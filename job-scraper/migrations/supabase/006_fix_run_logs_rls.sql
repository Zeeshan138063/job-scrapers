-- 006_fix_run_logs_rls.sql

-- Enable RLS for runs and alerts
ALTER TABLE scraper_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE scraper_alerts ENABLE ROW LEVEL SECURITY;

-- Allow unrestricted access (since we are in internal dev mode / service role context)
-- In production, you might restrict this to authenticated users or service roles.
CREATE POLICY "Enable all access for scraper_runs" ON scraper_runs FOR ALL USING (true);
CREATE POLICY "Enable all access for scraper_alerts" ON scraper_alerts FOR ALL USING (true);
