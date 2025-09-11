#!/usr/bin/env python3
"""
Test Fixed Discord Endpoints
"""

import requests

base_url = "https://org-admin-revamp.preview.emergentagent.com"
api_key = "210303df-9dbd-4bd3-add6-62e4e7b05977"  # The API key we added to the guild

def test_fixed_endpoints():
    """Test the fixed Discord endpoints"""
    
    print("🔍 Testing Fixed Discord Endpoints")
    print("="*50)
    
    # Test 1: Guild Config with correct API key
    print("\n--- Test 1: Guild Config (Correct API Key) ---")
    url = f"{base_url}/api/v1/discord/bot/guild/123456789012345678/config?api_key={api_key}"
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Guild config endpoint working!")
        elif response.status_code == 401:
            print("⚠️  Authentication failed - API key mismatch")
        
    except Exception as e:
        print(f"Request failed: {e}")
    
    # Test 2: Bot Verify with query parameters
    print("\n--- Test 2: Bot Verify (Query Parameters) ---")
    url = f"{base_url}/api/v1/discord/bot/verify?guild_id=123456789012345678&api_key={api_key}"
    
    try:
        response = requests.post(url, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Bot verify endpoint working!")
        elif response.status_code == 401:
            print("⚠️  Authentication failed - API key mismatch")
        
    except Exception as e:
        print(f"Request failed: {e}")
    
    # Test 3: Guild Registration
    print("\n--- Test 3: Guild Registration ---")
    url = f"{base_url}/api/v1/discord/bot/guild/999888777666555444/register"
    data = {
        "guild_name": "New Test Guild",
        "guild_icon": "https://example.com/icon.png",
        "owner_id": "111222333444555666",
        "member_count": 75,
        "setup_by_user_id": "user456",
        "bot_auto_registered": True
    }
    
    try:
        response = requests.post(url, json=data, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Guild registration working!")
        
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_fixed_endpoints()