
import json
from bs4 import BeautifulSoup

def analyze_html(file_path):
    with open(file_path, "r") as f:
        html = f.read()
    
    soup = BeautifulSoup(html, "lxml")
    
    print("--- JSON-LD Data ---")
    scripts = soup.find_all("script", {"type": "application/ld+json"})
    for i, script in enumerate(scripts):
        try:
            data = json.loads(script.string)
            print(f"Script {i+1}:")
            print(json.dumps(data, indent=2))
        except Exception as e:
            print(f"Error parsing script {i+1}: {e}")

    print("\n--- DOM Data ---")
    # Try the selectors from JobExtractor
    job_card = soup.find("div", {"data-testid": "job-preview-card"})
    if job_card:
        print("Found job-preview-card!")
        print("Title:", job_card.find("h1").get_text(strip=True) if job_card.find("h1") else "N/A")
        print("Company:", job_card.find("h2").get_text(strip=True) if job_card.find("h2") else "N/A")
        salary = job_card.find("div", {"data-testid": "job-card-chip-salary"})
        print("Salary:", salary.get_text(strip=True) if salary else "N/A")
    else:
        print("job-preview-card NOT found.")
        # Fallback search
        h1 = soup.find("h1")
        print("First H1:", h1.get_text(strip=True) if h1 else "N/A")

if __name__ == "__main__":
    analyze_html("scrapers/spiders/job_detail.html")
