#!/usr/bin/env python3
"""
Test script to verify the analytics endpoint fix
"""

import requests
import json

def test_analytics_endpoint():
    """Test the analytics dashboard endpoint"""
    
    # Test with admin user (should work)
    try:
        # First login to get a token
        login_response = requests.post('http://localhost:3001/api/users/login', 
                                     json={
                                         'email': 'admin@example.com',
                                         'password': 'admin123'
                                     })
        
        if login_response.status_code == 200:
            login_data = login_response.json()
            print(f"📝 Login response: {login_data}")
            token = login_data.get('data', {}).get('token')
            
            if token:
                print("✅ Admin login successful")
                
                # Test analytics endpoint
                headers = {'Authorization': f'Bearer {token}'}
                analytics_response = requests.get('http://localhost:3001/api/analytics/dashboard', 
                                                headers=headers)
                
                if analytics_response.status_code == 200:
                    analytics_data = analytics_response.json()
                    print("✅ Analytics endpoint successful")
                    print(f"📊 Data source: {analytics_data.get('data_source', 'unknown')}")
                    
                    # Check for critical data structure
                    if analytics_data.get('success') and analytics_data.get('data'):
                        data = analytics_data['data']
                        print(f"✅ Has userRegistrations: {bool(data.get('userRegistrations'))}")
                        print(f"✅ Has orderStats: {bool(data.get('orderStats'))}")
                        print(f"✅ Has systemMetrics: {bool(data.get('systemMetrics'))}")
                        print(f"✅ Has quickActions: {bool(data.get('quickActions'))}")
                        
                        # Check nested structure that was causing the error
                        user_reg = data.get('userRegistrations', {})
                        if isinstance(user_reg, dict) and 'data' in user_reg:
                            print(f"✅ userRegistrations.data: {user_reg['data']}")
                        else:
                            print(f"❌ userRegistrations structure: {type(user_reg)} - {user_reg}")
                            
                        quick_actions = data.get('quickActions', {})
                        if isinstance(quick_actions, dict):
                            print(f"✅ quickActions.pendingOrders: {quick_actions.get('pendingOrders', 'N/A')}")
                            print(f"✅ quickActions.lowStockProducts: {quick_actions.get('lowStockProducts', 'N/A')}")
                        
                        return True
                    else:
                        print("❌ Missing success or data in response")
                        return False
                else:
                    print(f"❌ Analytics endpoint failed: {analytics_response.status_code}")
                    print(f"Response: {analytics_response.text}")
                    return False
            else:
                print("❌ No token received from login")
                return False
        else:
            print(f"❌ Login failed: {login_response.status_code}")
            print(f"Response: {login_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing analytics: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Analytics Endpoint Fix...")
    print("=" * 50)
    
    success = test_analytics_endpoint()
    
    print("=" * 50)
    if success:
        print("🎉 Analytics endpoint test PASSED!")
        print("The undefined data property error should now be fixed.")
    else:
        print("💥 Analytics endpoint test FAILED!")
        print("The issue may still exist or there are other problems.")
