#!/usr/bin/env python3
"""
Test script to verify analytics dashboard endpoint and quick actions
"""
import requests
import json

# Configuration
BASE_URL = "http://localhost:3001/api"
TEST_ADMIN_CREDENTIALS = {
    "email": "admin@example.com", 
    "password": "admin123"
}

def test_analytics_dashboard():
    """Test analytics dashboard endpoint"""
    print("🔐 Testing admin login...")
    try:
        response = requests.post(f"{BASE_URL}/auth/login", 
                               json=TEST_ADMIN_CREDENTIALS,
                               timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                token = data.get('token')
                print("✅ Admin login successful")
                
                print("\n📊 Testing analytics dashboard...")
                headers = {"Authorization": f"Bearer {token}"}
                
                response = requests.get(f"{BASE_URL}/analytics/dashboard",
                                      headers=headers,
                                      timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        print("✅ Analytics dashboard endpoint working")
                        
                        # Check for quick actions
                        quick_actions = data.get('data', {}).get('quickActions', {})
                        if quick_actions:
                            print(f"✅ Quick actions found:")
                            print(f"   - Pending Orders: {quick_actions.get('pendingOrders', 'N/A')}")
                            print(f"   - Low Stock Products: {quick_actions.get('lowStockProducts', 'N/A')}")
                        else:
                            print("❌ Quick actions not found in response")
                            print(f"   Available keys: {list(data.get('data', {}).keys())}")
                        
                        # Check for other analytics data
                        analytics_data = data.get('data', {})
                        expected_keys = ['userRegistrations', 'orderStats', 'topProducts', 'systemMetrics']
                        for key in expected_keys:
                            if key in analytics_data:
                                print(f"✅ {key} data present")
                            else:
                                print(f"❌ {key} data missing")
                                
                    else:
                        print(f"❌ Analytics request failed: {data.get('message')}")
                else:
                    print(f"❌ Analytics request failed with status {response.status_code}")
                    print(f"   Response: {response.text}")
            else:
                print(f"❌ Login failed: {data.get('message')}")
        else:
            print(f"❌ Login failed with status {response.status_code}")
    except Exception as e:
        print(f"❌ Test error: {e}")

def main():
    print("🧪 Analytics Dashboard Test")
    print("=" * 40)
    test_analytics_dashboard()
    print("\n✅ Test completed!")

if __name__ == "__main__":
    main()
