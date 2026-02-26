import os
import sys
import json

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scrapers.utils.credential_manager import CredentialManager

def test_credential_manager():
    creds_path = "config/jobleads_creds.json"
    cm = CredentialManager(creds_path)
    
    # Check initial state
    configs = cm.get_configs_for_startup("ARG")
    print(f"Initial ARG config count: {len(configs)}")
    if configs:
        email = configs[0]['email']
        print(f"Blocking {email} for ARG...")
        cm.mark_blocked("ARG", email, "test_reason")
        
        # Verify it's gone
        new_configs = cm.get_configs_for_startup("ARG")
        print(f"New ARG config count: {len(new_configs)}")
        
        # Verify JSON file has 'is_blocked': True
        with open(creds_path, 'r') as f:
            data = json.load(f)
            if data["ARG"].get("is_blocked"):
                print("✅ Successfully marked ARG as blocked in JSON.")
            else:
                print("❌ Failed to mark ARG as blocked in JSON.")
                
        # Cleanup: Unblock for future real runs (since this is a test)
        data["ARG"]["is_blocked"] = False
        if "block_reason" in data["ARG"]: del data["ARG"]["block_reason"]
        if "blocked_at" in data["ARG"]: del data["ARG"]["blocked_at"]
        with open(creds_path, 'w') as f:
            json.dump(data, f, indent=4)
        print("Restored ARG state.")
    else:
        print("No configs found for ARG.")

if __name__ == "__main__":
    test_credential_manager()
