import json
import logging
import os
import threading
from typing import Optional, Dict, List, Any

logger = logging.getLogger(__name__)

class CredentialManager:
    """
    Manages JobLeads credentials across multiple countries.
    Supports account rotation and permanent/temporary blocking.
    """
    def __init__(self, creds_path: str):
        self.creds_path = creds_path
        self.lock = threading.Lock()
        self.creds = self._load()

    def _load(self) -> Dict[str, Any]:
        """Loads credentials from JSON file."""
        if not os.path.exists(self.creds_path):
            logger.error(f"Credentials file not found: {self.creds_path}")
            return {}
        try:
            logger.info(f"Loading credentials from: {self.creds_path}")
            with open(self.creds_path, 'r') as f:
                data = json.load(f)
                logger.info(f"Loaded {len(data)} countries from JSON.")
                return data
        except Exception as e:
            logger.error(f"Failed to load credentials from {self.creds_path}: {e}")
            return {}

    def _save(self):
        """Persists credentials back to JSON file."""
        with self.lock:
            try:
                with open(self.creds_path, 'w') as f:
                    json.dump(self.creds, f, indent=4)
            except Exception as e:
                logger.error(f"Failed to save credentials to {self.creds_path}: {e}")

    def get_credentials(self, country_code: str) -> List[Dict[str, Any]]:
        """Returns all available (non-blocked) credentials for a country."""
        country_code = country_code.upper()
        if country_code not in self.creds:
            return []
        
        creds_data = self.creds[country_code]
        
        # If the data is already a list of credentials
        if isinstance(creds_data, list):
            return [c for c in creds_data if not c.get("is_blocked")]
        
        # If the data is a single dictionary (current format)
        if isinstance(creds_data, dict):
            if not creds_data.get("is_blocked"):
                return [creds_data]
        
        return []

    def mark_blocked(self, country_code: str, email: str, reason: str = "blocked"):
        """Marks a specific credential as blocked and persists the change."""
        country_code = country_code.upper()
        if country_code not in self.creds:
            return

        creds_list = self.creds[country_code]
        if isinstance(creds_list, dict):
            if creds_list.get("email") == email:
                creds_list["is_blocked"] = True
                creds_list["block_reason"] = reason
                creds_list["blocked_at"] = os.popen('date').read().strip()
        else:
            for cred in creds_list:
                if cred.get("email") == email:
                    cred["is_blocked"] = True
                    cred["block_reason"] = reason
                    cred["blocked_at"] = os.popen('date').read().strip()
                    break
        
        self._save()
        logger.warning(f"🚫 Account {email} for {country_code} marked as {reason}!")

    def get_configs_for_startup(self, country_arg: Optional[str] = None) -> List[Dict[str, Any]]:
        """Utility for spider startup to get all valid country/email pairs."""
        configs = []
        target_countries = [country_arg.upper()] if country_arg else self.creds.keys()
        
        logger.debug(f"Startup targeted countries: {target_countries}")
        for code in target_countries:
            if code not in self.creds:
                logger.warning(f"Country {code} not found in credentials keys: {list(self.creds.keys())}")
                continue
                
            available = self.get_credentials(code)
            logger.info(f"Found {len(available)} available credentials for {code}")
            for conf in available:
                conf['country_code'] = code
                configs.append(conf)
                
        return configs
