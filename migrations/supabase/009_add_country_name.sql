-- Add country_name column to potential tables
ALTER TABLE job_listings ADD COLUMN IF NOT EXISTS country_name TEXT;
ALTER TABLE scraper_job_listings ADD COLUMN IF NOT EXISTS country_name TEXT;

-- Update existing records if needed (optional)
-- UPDATE scraper_job_listings SET country_name = 'Unknown' WHERE country_name IS NULL;
