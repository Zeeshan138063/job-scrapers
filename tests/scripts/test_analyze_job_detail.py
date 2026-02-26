
import json
import os
from bs4 import BeautifulSoup

def analyze_html(file_path):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    with open(file_path, "r") as f:
        html = f.read()
    
    soup = BeautifulSoup(html, "lxml")
    
    print("--- 1. JSON-LD Data ---")
    scripts = soup.find_all("script", {"type": "application/ld+json"})
    found_json_ld = False
    for i, script in enumerate(scripts):
        try:
            if not script.string:
                continue
            data = json.loads(script.string)
            print(f"Script {i+1}:")
            # print(json.dumps(data, indent=2))
            if isinstance(data, dict) and data.get("@type") == "JobPosting":
                print(f"  Type: JobPosting")
                print(f"  Title: {data.get('title')}")
                print(f"  Company: {data.get('hiringOrganization', {}).get('name')}")
                print(f"  URL (JSON-LD): {data.get('url')}")
            else:
                print(f"  Type: {type(data)}")
            found_json_ld = True
        except Exception as e:
            print(f"Error parsing script {i+1}: {e}")
            
    if not found_json_ld:
        print("No JSON-LD found.")

    print("\n--- 2. DOM Data ---")
    # Try the selectors from JobExtractor
    job_card = soup.find("div", {"data-testid": "job-preview-card"})
    if job_card:
        print("Found job-preview-card!")
        title_tag = job_card.find("h1")
        if title_tag:
             print("Title:", title_tag.get_text(strip=True))
        
        company_tag = job_card.find("h2")
        # if company_tag:
        #      print("Company:", company_tag.get_text(strip=True))
        
    else:
        print("job-preview-card NOT found.")
        # Fallback search
        h1 = soup.find("h1")
        if h1:
            print("First H1:", h1.get_text(strip=True))

    print("\n--- 3. Apply Actions / URLs ---")
    # Finding elements related to apply, links, buttons
    apply_links = []
    # Check for links with apply in text or href
    for a in soup.find_all("a", href=True):
        href = a['href']
        text = a.get_text(strip=True).lower()
        if "apply" in text or "apply" in href:
            apply_links.append({"text": text, "href": href})
            
    # Check for buttons that might be apply buttons
    buttons = soup.find_all("button")
    for btn in buttons:
        text = btn.get_text(strip=True).lower()
        if "apply" in text:
            print(f"Found Apply Button: text='{btn.get_text(strip=True)}', attrs={btn.attrs}")
            # Check if button is wrapped in a link
            parent = btn.find_parent("a")
            if parent:
                print(f"  Parent Link: {parent['href']}")

    if apply_links:
        print("Found Apply Links:")
        for link in apply_links:
            print(f"  - Text: '{link['text']}', Href: {link['href']}")
    else:
        print("No explicit 'Apply' links found.")

    # Check specific JobLeads structure for external apply
    # Sometimes it's in a data attribute or script
    print("\n--- 4. JobLeads Specifics ---")
    # Look for the apply button container
    apply_container = soup.find("div", class_="apply-button-container")
    if apply_container:
        print("Found apply-button-container")
    
    # Check for Nuxt data if present (often JobLeads is Nuxt)
    # scripts = soup.find_all("script")
    # for s in scripts:
    #     if s.string and "window.__NUXT__" in s.string:
    #         print("Found Nuxt state script (might contain data)")


if __name__ == "__main__":
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    html_path = os.path.join(base_dir, "tests/data/job_detail.html")
    analyze_html(html_path)
