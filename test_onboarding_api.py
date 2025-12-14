#!/usr/bin/env python3
"""
Simple test for onboarding goals API
Usage: python test_onboarding_api.py
"""

import httpx
import json

BASE_URL = "http://localhost:8000"

def test_get_goals():
    """Test fetching onboarding goals"""
    try:
        response = httpx.get(f"{BASE_URL}/onboarding/goals", timeout=10.0)
        response.raise_for_status()
        
        data = response.json()
        print("✅ Success!")
        print(f"Response: {json.dumps(data, indent=2)}")
        return True
    except httpx.ConnectError:
        print("❌ Error: Server not running. Start with: python -m app.main")
        return False
    except httpx.HTTPStatusError as e:
        print(f"❌ Error: {e.response.status_code}")
        print(f"Response: {e.response.text}")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    test_get_goals()
