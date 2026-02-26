-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create the generic job_listings table
CREATE TABLE IF NOT EXISTS public.job_listings (
    -- --- IDENTITY ---
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_id TEXT NOT NULL,          -- Source ID (e.g. "e8fa00cc...")
    source_domain TEXT NOT NULL,        -- Domain where scraping happened (e.g. "jobleads.com")
    url TEXT,                           -- Full Canonical URL
    source_url TEXT,                    -- Original source URL (e.g. LinkedIn)
    
    -- --- HEADER INFO ---
    title TEXT NOT NULL,
    company_name TEXT,
    
    -- --- LOCATION ---
    location_raw TEXT,                  -- "Moreno" (API 1 original)
    city TEXT,                          -- "Moreno"
    region TEXT,                        -- "Buenos Aires"
    country_code TEXT,                  -- "AR" (ISO 2-char)
    
    -- --- WORK DETAILS ---
    employment_type TEXT,               -- "full_time" (API 1 contractType)
    remote_modality TEXT,               -- "hybrid", "remote", "on_site" (API 1 isRemote)
    
    -- --- SALARY ---
    salary_raw TEXT,                    -- "ARS 9.7M - 12.5M"
    salary_min NUMERIC,                 -- 9750000
    salary_max NUMERIC,                 -- 12500000
    salary_currency TEXT,               -- "ARS"
    salary_period TEXT,                 -- "YEAR" (salary_unit)

    -- --- DESCRIPTION ---
    description_short TEXT,             -- API 2 jobSummary
    description_html TEXT,              -- API 3 full HTML
    description_text TEXT,              -- Optional plain text
    
    -- --- LISTS (Structured Data - JSONB) ---
    benefits JSONB,                     -- ["PTO", "RRSP", ...]
    skills JSONB,                       -- [{"text": "Leadership"}, ...]
    qualifications JSONB,               -- ["Experience leading..."]
    responsibilities JSONB,             -- ["Lead a cross-functional..."]
    education JSONB,
    tools JSONB,

    -- --- METADATA & FLAGS ---
    meta_flags JSONB DEFAULT '{}'::jsonb, 
    -- EXAMPLES: { "is_featured": false, "source_type": "jobboard" }

    -- --- AUDIT TRAIL ---
    scraped_source TEXT,                -- "job_leads_v1_scraper" (Internal tracker)
    hostname_origin TEXT,               -- "www.linkedin.com" (From API 2 hostname)
    raw_data JSONB,                     -- 100% full original JSON (Backup)
    
    -- --- TIMESTAMPS ---
    posted_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    last_scraped_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- --- CONSTRAINTS ---
    UNIQUE(external_id, source_domain)
);

-- --- INDEXES FOR PERFORMANCE ---

-- Filtering by Source (Admin/Analytics)
CREATE INDEX IF NOT EXISTS idx_jobs_source_domain ON public.job_listings(source_domain);
CREATE INDEX IF NOT EXISTS idx_jobs_scraped_source ON public.job_listings(scraped_source);

-- Geo Filtering (Common User Query)
CREATE INDEX IF NOT EXISTS idx_jobs_country_city ON public.job_listings(country_code, city);
CREATE INDEX IF NOT EXISTS idx_jobs_region ON public.job_listings(region);

-- Timeline (Sorting by Newest)
CREATE INDEX IF NOT EXISTS idx_jobs_posted_at ON public.job_listings(posted_at DESC);

-- Salary Filtering (Range Queries)
CREATE INDEX IF NOT EXISTS idx_jobs_salary_min ON public.job_listings(salary_min);
CREATE INDEX IF NOT EXISTS idx_jobs_salary_max ON public.job_listings(salary_max);

-- Remote/Type Filtering
CREATE INDEX IF NOT EXISTS idx_jobs_work_type ON public.job_listings(remote_modality, employment_type);

-- Advanced JSONB Search (Skills/Metadata)
CREATE INDEX IF NOT EXISTS idx_jobs_skills_gin ON public.job_listings USING gin(skills);
CREATE INDEX IF NOT EXISTS idx_jobs_metadata_gin ON public.job_listings USING gin(meta_flags);

-- Full Text Search
CREATE INDEX IF NOT EXISTS idx_jobs_title_fts ON public.job_listings USING GIN (to_tsvector('english', title));
