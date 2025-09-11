#!/usr/bin/env python3
"""
Final Discord Test - Test all fixed endpoints
"""

import requests
import json

base_url = "https://org-admin-revamp.preview.emergentagent.com"
api_key = "210303df-9dbd-4bd3-add6-62e4e7b05977"  # The API key we added to the guild

def test_all_discord_endpoints():
    """Test all Discord endpoints with correct parameters"""
    
    print("🔍 FINAL DISCORD ENDPOINTS TEST")
    print("="*50)
    
    # Test 1: Bot Verify with JSON body
    print("\n--- Test 1: Bot Verify (JSON Body) ---")
    url = f"{base_url}/api/v1/discord/bot/verify"
    data = {
        "guild_id": "123456789012345678",
        "api_key": api_key
    }
    
    try:
        response = requests.post(url, json=data, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Bot verify endpoint working!")
        elif response.status_code == 401:
            print("⚠️  Authentication failed - API key mismatch")
        
    except Exception as e:
        print(f"Request failed: {e}")
    
    # Test 2: Guild Config with query parameter
    print("\n--- Test 2: Guild Config (Query Parameter) ---")
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
    
    # Test 3: Guild Registration (new guild)
    print("\n--- Test 3: Guild Registration (New Guild) ---")
    url = f"{base_url}/api/v1/discord/bot/guild/111222333444555666/register"
    data = {
        "guild_name": "Another Test Guild",
        "guild_icon": "https://example.com/icon2.png",
        "owner_id": "777888999000111222",
        "member_count": 42,
        "setup_by_user_id": "user789",
        "bot_auto_registered": True
    }
    
    try:
        response = requests.post(url, json=data, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Guild registration working!")
            # Extract the API key for further testing
            response_data = response.json()
            new_api_key = response_data.get("api_key")
            if new_api_key:
                print(f"📝 New guild API key: {new_api_key}")
                
                # Test the new guild's config endpoint
                print("\n--- Test 4: New Guild Config ---")
                config_url = f"{base_url}/api/v1/discord/bot/guild/111222333444555666/config?api_key={new_api_key}"
                config_response = requests.get(config_url, timeout=10)
                print(f"New Guild Config Status: {config_response.status_code}")
                if config_response.status_code == 200:
                    print("✅ New guild config working!")
                else:
                    print(f"Response: {config_response.text}")
        
    except Exception as e:
        print(f"Request failed: {e}")
    
    # Test 5: Invalid API key scenarios
    print("\n--- Test 5: Invalid API Key Scenarios ---")
    
    # Test with wrong API key
    wrong_data = {
        "guild_id": "123456789012345678",
        "api_key": "wrong-api-key"
    }
    
    response = requests.post(f"{base_url}/api/v1/discord/bot/verify", json=wrong_data, timeout=10)
    print(f"Wrong API Key Status: {response.status_code} (Expected: 401)")
    
    # Test with missing parameters
    incomplete_data = {
        "guild_id": "123456789012345678"
        # Missing api_key
    }
    
    response = requests.post(f"{base_url}/api/v1/discord/bot/verify", json=incomplete_data, timeout=10)
    print(f"Missing API Key Status: {response.status_code} (Expected: 400)")

if __name__ == "__main__":
    test_all_discord_endpoints()