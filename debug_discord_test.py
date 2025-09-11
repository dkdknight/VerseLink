#!/usr/bin/env python3
"""
Debug Discord Endpoint Issues
"""

import requests
import json

base_url = "https://org-admin-revamp.preview.emergentagent.com"

def test_discord_config_endpoint():
    """Test the Discord config endpoint to see exact error"""
    
    print("Testing Discord Guild Config Endpoint...")
    
    # Test 1: With query parameter
    url = f"{base_url}/api/v1/discord/bot/guild/123456789012345678/config?api_key=test-key"
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Response: {response.text}")
        
        if response.status_code == 500:
            print("🚨 500 Error detected!")
            
    except Exception as e:
        print(f"Request failed: {e}")

def test_discord_verify_endpoint():
    """Test the Discord verify endpoint"""
    
    print("\nTesting Discord Bot Verify Endpoint...")
    
    url = f"{base_url}/api/v1/discord/bot/verify"
    data = {
        "guild_id": "123456789012345678",
        "api_key": "test-api-key"
    }
    
    try:
        response = requests.post(url, json=data, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_discord_config_endpoint()
    test_discord_verify_endpoint()