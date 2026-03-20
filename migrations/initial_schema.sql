-- Initial Schema: Job Listings Table
-- Consolidated from previous migrations

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS public.job_listings (
  id uuid not null default gen_random_uuid (),
  source text not null,
  external_id text not null,
  source_domain text not null,
  url text null,
  source_url text null,
  title text not null,
  company_name text null,
  location_raw text null,
  city text null,
  region text null,
  country_code text null,
  employment_type text null,
  remote_modality text null,
  salary_raw text null,
  salary_min numeric null,
  salary_max numeric null,
  salary_currency text null,
  salary_period text null,
  description_short text null,
  description_html text null,
  description_text text null,
  benefits jsonb null,
  skills jsonb null,
  qualifications jsonb null,
  responsibilities jsonb null,
  education jsonb null,
  tools jsonb null,
  meta_flags jsonb null default '{}'::jsonb,
  scraped_source text null,
  hostname_origin text null,
  raw_data jsonb null,
  posted_at timestamp with time zone null,
  expires_at timestamp with time zone null,
  last_scraped_at timestamp with time zone null default now(),
  created_at timestamp with time zone null default now(),
  updated_at timestamp with time zone null default now(),
  country_name text null,
  constraint job_listings_pkey1 primary key (id),
  constraint job_listings_external_id_source_domain_key1 unique (external_id, source_domain)
) TABLESPACE pg_default;

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_job_listings_external_source ON public.job_listings(external_id, source_domain);
CREATE INDEX IF NOT EXISTS idx_job_listings_title ON public.job_listings(title);
CREATE INDEX IF NOT EXISTS idx_job_listings_posted_at ON public.job_listings(posted_at DESC);
CREATE INDEX IF NOT EXISTS idx_job_listings_country ON public.job_listings(country_code, country_name);
CREATE INDEX IF NOT EXISTS idx_job_listings_salary ON public.job_listings(salary_min, salary_max);
