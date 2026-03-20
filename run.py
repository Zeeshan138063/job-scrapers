#!/usr/bin/env python3
"""
run.py — Entry point for the Job Scraper project.

Commands:
  worker  Start the full async worker + cron scheduler (requires Redis + Postgres)
  run     Run a specific spider directly (one-shot, no Redis required)
  seed    Initialize and seed the database with default configurations

Examples:
  python run.py worker
  python run.py run job_leads_v2
  python run.py run job_leads_v2 --queries "python developer" "django" --locations "NLD" "DEU"
  python run.py run job_leads_v2 --output results.json
  python run.py seed
"""

import argparse
import asyncio
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(__file__))


def cmd_worker(args):
    """Start the async worker + cron scheduler."""
    from worker.worker import ScrapingWorker
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    worker = ScrapingWorker(redis_url)
    print(f"Starting worker... (Redis: {redis_url})")
    try:
        asyncio.run(worker.run())
    except KeyboardInterrupt:
        print("\nWorker stopped.")


def cmd_run(args):
    """Run a spider directly in a subprocess (one-shot)."""
    os.environ.setdefault("SCRAPY_SETTINGS_MODULE", "scrapers.settings")
    from worker.worker import run_spider_process

    spider_args = {
        "search_queries": args.queries,
        "locations": args.locations,
    }

    if args.min_salary:
        spider_args["min_salary"] = args.min_salary

    settings_overrides = {}
    if args.output:
        fmt = "json" if args.output.endswith(".json") else "csv"
        settings_overrides["FEEDS"] = {args.output: {"format": fmt}}
    if args.limit:
        settings_overrides["CLOSESPIDER_ITEMCOUNT"] = args.limit

    print(f"Running spider: {args.spider}")
    print(f"  Queries   : {args.queries}")
    print(f"  Locations : {args.locations}")
    if args.output:
        print(f"  Output    : {args.output}")
    if args.limit:
        print(f"  Limit     : {args.limit} items")

    run_spider_process(args.spider, spider_args, settings_overrides)


def cmd_seed(args):
    """Initialize database tables and seed default spider configs."""
    import subprocess
    result = subprocess.run(
        [sys.executable, "scripts/seed_db.py"],
        env={**os.environ, "PYTHONPATH": "."},
    )
    sys.exit(result.returncode)


def main():
    parser = argparse.ArgumentParser(
        description="Job Scraper – control panel",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    subparsers = parser.add_subparsers(dest="command", metavar="command")
    subparsers.required = True

    # --- worker command ---
    subparsers.add_parser(
        "worker",
        help="Start the async worker + cron scheduler",
    )

    # --- run command ---
    run_parser = subparsers.add_parser(
        "run",
        help="Run a specific spider directly (one-shot)",
    )
    run_parser.add_argument(
        "spider",
        help="Spider name (e.g. job_leads_v2, linkedin_jobs)",
    )
    run_parser.add_argument(
        "--queries", "-q",
        nargs="+",
        default=["python"],
        metavar="QUERY",
        help="Search keywords (default: python)",
    )
    run_parser.add_argument(
        "--locations", "-l",
        nargs="+",
        default=["NLD"],
        metavar="LOC",
        help="Locations or country codes (default: NLD)",
    )
    run_parser.add_argument(
        "--output", "-o",
        default=None,
        metavar="FILE",
        help="Output file path (e.g. results.json or results.csv)",
    )
    run_parser.add_argument(
        "--limit", "-n",
        type=int,
        default=None,
        metavar="N",
        help="Stop after scraping N items",
    )
    run_parser.add_argument(
        "--min-salary",
        type=int,
        default=None,
        metavar="SALARY",
        help="Minimum salary filter",
    )

    # --- seed command ---
    subparsers.add_parser(
        "seed",
        help="Initialize database tables and seed default configurations",
    )

    args = parser.parse_args()

    dispatch = {
        "worker": cmd_worker,
        "run": cmd_run,
        "seed": cmd_seed,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
