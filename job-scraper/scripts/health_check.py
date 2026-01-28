import requests
import sys

def check_scraper_health(url='http://localhost:9410'):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            print(f"✅ Scraper worker is UP (Metrics endpoint accessible at {url})")
            # Rudimentary check for content
            if 'scrapy_items_scraped_total' in response.text:
                 print("✅ Metrics are being exported")
            return True
        else:
            print(f"❌ Scraper worker returned status code {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Could not connect to Scraper worker at {url}")
        return False

if __name__ == "__main__":
    success = check_scraper_health()
    sys.exit(0 if success else 1)
