import json
import subprocess
import time
import os
import sys

# Path to our credentials file
CONFIG_FILE = "config/jobleads_creds.json"
# "/home/zeeshan/projects/job-scrapers/scripts/run_parallel_jobleads.py"
def main():
    if not os.path.exists(CONFIG_FILE):
        print(f"❌ Config file not found: {CONFIG_FILE}")
        sys.exit(1)

    with open(CONFIG_FILE, "r") as f:
        data = json.load(f)

    # Dictionary of processes
    processes = []

    print(f"🚀 Starting {len(data)} scrapers in parallel...")
    
    for country_code in data.keys():
        print(f"Starting spider for: {country_code}")
        
        # Build command: scrapy crawl jobleads -a country=XX
        cmd = ["scrapy", "crawl", "jobleads", "-a", f"country={country_code}"]
        
        # Start detached process
        p = subprocess.Popen(cmd)
        processes.append(p)
        
        # Stagger start times to avoid initial thundering herd
        # time.sleep(1)

    print(f"✅ All {len(processes)} scrapers launched.")
    
    # Wait for all? Or just exit?
    # Ideally, we wait or use supervisord. For this script, we'll wait.
    try:
        for p in processes:
            p.wait()
    except KeyboardInterrupt:
        print("\n🛑 Stopping all scrapers...")
        for p in processes:
            p.terminate()

if __name__ == "__main__":
    main()
