import json
import os
import requests
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MoltbookUpdater")

API_BASE = "https://www.moltbook.com/api/v1"
CREDENTIALS_PATH = os.path.expanduser("~/.config/moltbook/credentials.json")

def load_api_key():
    try:
        with open(CREDENTIALS_PATH, 'r') as f:
            data = json.load(f)
            return data.get("api_key")
    except Exception as e:
        logger.error(f"Failed to load credentials: {e}")
        return None

def update_username(new_name):
    api_key = load_api_key()
    if not api_key:
        return
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # 1. Get current profile to verify endpoint
    try:
        logger.info("Checking current profile...")
        resp = requests.get(f"{API_BASE}/me", headers=headers)
        if resp.status_code == 200:
            user_data = resp.json()
            logger.info(f"Current Profile: {user_data}")
        elif resp.status_code == 404:
            # Try /user/me
            resp = requests.get(f"{API_BASE}/user/me", headers=headers)
            if resp.status_code == 200:
                user_data = resp.json()
                logger.info(f"Current Profile: {user_data}")
            else:
                logger.error(f"Could not fetch profile: {resp.status_code} {resp.text}")
                return
    except Exception as e:
        logger.error(f"Connection error: {e}")
        return

    # 2. Update Username
    try:
        logger.info(f"Attempting to change username to '{new_name}'...")
        payload = {"username": new_name}
        
        # Try PATCH /me
        resp = requests.patch(f"{API_BASE}/me", headers=headers, json=payload)
        
        if resp.status_code == 200:
            logger.info("✅ Username updated successfully!")
            logger.info(resp.json())
            
            # Update local file too
            with open(CREDENTIALS_PATH, 'r+') as f:
                data = json.load(f)
                data["agent_name"] = new_name
                f.seek(0)
                json.dump(data, f, indent=4)
                f.truncate()
                
        else:
            logger.error(f"❌ Update failed: {resp.status_code} {resp.text}")
            
    except Exception as e:
        logger.error(f"Update error: {e}")

if __name__ == "__main__":
    update_username("Nexara")
