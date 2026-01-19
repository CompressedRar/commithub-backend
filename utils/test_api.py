"""
Quick API testing script for manual endpoint validation.
Usage: python backend/utils/test_api.py
"""

import sys
import os
import json
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app
from config import TestConfig

app = create_app(TestConfig)
client = app.test_client()

def test_endpoint(method, endpoint, data=None, headers=None):
    """Test single endpoint."""
    print(f"\n📍 {method.upper()} {endpoint}")
    try:
        if method == 'GET':
            response = client.get(endpoint, headers=headers)
        elif method == 'POST':
            response = client.post(endpoint, json=data, headers=headers)
        elif method == 'PATCH':
            response = client.patch(endpoint, json=data, headers=headers)
        elif method == 'DELETE':
            response = client.delete(endpoint, headers=headers)
        
        print(f"   Status: {response.status_code}")
        try:
            print(f"   Response: {json.dumps(response.json, indent=2)}")
        except:
            print(f"   Response: {response.data.decode()}")
        
        return response
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return None

def run_tests():
    """Run sample tests on key endpoints."""
    print("="*60)
    print("TESTING PUBLIC ENDPOINTS")
    print("="*60)
    
    with app.app_context():
        # Public endpoints (no auth)
        test_endpoint('GET', '/api/v1/departments')
        test_endpoint('GET', '/api/v1/categories')
        test_endpoint('GET', '/api/v1/tasks')
        test_endpoint('GET', '/api/v1/settings')
        
        print("\n" + "="*60)
        print("TESTING PROTECTED ENDPOINTS (should fail without auth)")
        print("="*60)
        
        test_endpoint('GET', '/api/v1/users/profile')
        test_endpoint('GET', '/api/v1/logs')
        
        print("\n✅ Testing complete!")

if __name__ == '__main__':
    run_tests()
