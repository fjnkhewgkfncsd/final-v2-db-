#!/usr/bin/env python3
"""
Test script to verify staff role restrictions and functionality
"""
import requests
import json

# Configuration
BASE_URL = "http://localhost:3001/api"
TEST_STAFF_CREDENTIALS = {
    "email": "staff@example.com",
    "password": "staff123"
}

def test_staff_login():
    """Test staff user login"""
    print("🔐 Testing staff login...")
    try:
        response = requests.post(f"{BASE_URL}/auth/login", 
                               json=TEST_STAFF_CREDENTIALS,
                               timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Staff login successful")
                return data.get('token')
            else:
                print(f"❌ Login failed: {data.get('message')}")
                return None
        else:
            print(f"❌ Login failed with status {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def test_query_execution(token):
    """Test that staff can execute SELECT queries but not INSERT/UPDATE/DELETE"""
    print("\n🔍 Testing query execution permissions...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test 1: Valid SELECT query (should work)
    select_query = {
        "sql": "SELECT name, stock_quantity FROM products LIMIT 5;"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/database/execute-query",
                               json=select_query,
                               headers=headers,
                               timeout=10)
        
        if response.status_code == 200:
            print("✅ SELECT query execution allowed for staff")
        else:
            print(f"❌ SELECT query failed: {response.status_code}")
    except Exception as e:
        print(f"❌ SELECT query error: {e}")
    
    # Test 2: INSERT query (should be blocked)
    insert_query = {
        "sql": "INSERT INTO products (name) VALUES ('test');"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/database/execute-query",
                               json=insert_query,
                               headers=headers,
                               timeout=10)
        
        if response.status_code == 403:
            print("✅ INSERT query correctly blocked for staff")
        else:
            print(f"❌ INSERT query should be blocked but got: {response.status_code}")
    except Exception as e:
        print(f"❌ INSERT query test error: {e}")

def test_restricted_endpoints(token):
    """Test that staff cannot access admin-only endpoints"""
    print("\n🚫 Testing restricted endpoint access...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test database stats (admin only)
    try:
        response = requests.get(f"{BASE_URL}/database/stats",
                              headers=headers,
                              timeout=10)
        
        if response.status_code == 403:
            print("✅ Database stats correctly blocked for staff")
        else:
            print(f"❌ Database stats should be blocked but got: {response.status_code}")
    except Exception as e:
        print(f"❌ Database stats test error: {e}")
    
    # Test analytics (should now be admin only)
    try:
        response = requests.get(f"{BASE_URL}/analytics/performance",
                              headers=headers,
                              timeout=10)
        
        if response.status_code == 403:
            print("✅ Analytics performance correctly blocked for staff")
        else:
            print(f"❌ Analytics performance should be blocked but got: {response.status_code}")
    except Exception as e:
        print(f"❌ Analytics performance test error: {e}")

def test_dashboard_access(token):
    """Test that staff get limited dashboard data"""
    print("\n📊 Testing dashboard access...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/analytics/dashboard",
                              headers=headers,
                              timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                # Check if data contains only quickActions (staff view)
                dashboard_data = data.get('data', {})
                if 'quickActions' in dashboard_data and len(dashboard_data) == 1:
                    print("✅ Staff dashboard returns only quick actions")
                else:
                    print("❌ Staff dashboard should only contain quickActions")
                    print(f"   Actual keys: {list(dashboard_data.keys())}")
            else:
                print(f"❌ Dashboard request failed: {data.get('message')}")
        else:
            print(f"❌ Dashboard request failed with status: {response.status_code}")
    except Exception as e:
        print(f"❌ Dashboard test error: {e}")

def main():
    print("🧪 Staff Role Restrictions Test")
    print("=" * 40)
    
    # Login as staff
    token = test_staff_login()
    if not token:
        print("❌ Cannot proceed without valid staff token")
        return
    
    # Run tests
    test_query_execution(token)
    test_restricted_endpoints(token)
    test_dashboard_access(token)
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    main()
