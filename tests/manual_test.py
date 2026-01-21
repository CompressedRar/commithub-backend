"""
Simple HTTP testing script using requests library.
Run with: python backend/tests/manual_test.py
"""

import requests
import json
from typing import Optional, Dict, Any

BASE_URL = "http://127.0.0.1:5000"

class APITester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.token = None
        self.session = requests.Session()
    
    def login(self, email: str, password: str) -> bool:
        """Authenticate and store token."""
        try:
            resp = self.post("/api/v1/auth/login", {
                "email": email,
                "password": password
            })
            if resp and resp.status_code == 200:
                self.token = resp.json().get("token")
                print(f"✅ Login successful. Token: {self.token[:20]}...")
                return True
            else:
                print(f"❌ Login failed: {resp.json() if resp else 'No response'}")
                return False
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False
    
    def get_headers(self) -> Dict:
        """Get request headers with token if available."""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Optional[requests.Response]:
        """GET request."""
        try:
            url = f"{self.base_url}{endpoint}"
            resp = self.session.get(url, headers=self.get_headers(), params=params)
            self._print_response(resp, "GET")
            return resp
        except Exception as e:
            print(f"❌ GET {endpoint} error: {e}")
            return None
    
    def post(self, endpoint: str, data: Dict) -> Optional[requests.Response]:
        """POST request."""
        try:
            url = f"{self.base_url}{endpoint}"
            resp = self.session.post(url, headers=self.get_headers(), json=data)
            self._print_response(resp, "POST")
            return resp
        except Exception as e:
            print(f"❌ POST {endpoint} error: {e}")
            return None
    
    def patch(self, endpoint: str, data: Dict) -> Optional[requests.Response]:
        """PATCH request."""
        try:
            url = f"{self.base_url}{endpoint}"
            resp = self.session.patch(url, headers=self.get_headers(), json=data)
            self._print_response(resp, "PATCH")
            return resp
        except Exception as e:
            print(f"❌ PATCH {endpoint} error: {e}")
            return None
    
    def delete(self, endpoint: str) -> Optional[requests.Response]:
        """DELETE request."""
        try:
            url = f"{self.base_url}{endpoint}"
            resp = self.session.delete(url, headers=self.get_headers())
            self._print_response(resp, "DELETE")
            return resp
        except Exception as e:
            print(f"❌ DELETE {endpoint} error: {e}")
            return None
    
    def _print_response(self, resp: requests.Response, method: str):
        """Pretty print response."""
        status_icon = "✅" if resp.status_code < 400 else "❌"
        print(f"\n{status_icon} {method} {resp.url}")
        print(f"   Status: {resp.status_code}")
        
        try:
            data = resp.json()
            print(f"   Response: {json.dumps(data, indent=2)}")
        except:
            print(f"   Response: {resp.text[:200]}")


def run_tests():
    """Run comprehensive API tests."""
    tester = APITester()
    
    print("\n" + "="*60)
    print("COMMITHUB API TESTING")
    print("="*60)
    
    # Test 1: Public endpoints (no auth)
    print("\n📌 TEST 1: PUBLIC ENDPOINTS")
    print("-" * 60)

    
    print("\n1. Get all departments:")
    tester.get("/api/v1/department")
    
    print("\n2. Get all categories:")
    tester.get("/api/v1/category")
    
    print("\n3. Get system settings:")
    tester.get("/api/v1/settings")
    
    # Test 2: Error handling
    print("\n\n📌 TEST 2: ERROR HANDLING")
    print("-" * 60)
    
    print("\n1. Test 404 (nonexistent endpoint):")
    tester.get("/api/v1/nonexistent")
    
    print("\n2. Test 401 (protected route without auth):")
    tester.get("/api/v1/log")
    
    print("\n3. Test invalid data:")
    tester.post("/api/v1/auth/login", {"email": "", "password": ""})
    
    # Test 3: Authentication flow
    print("\n\n📌 TEST 3: AUTHENTICATION FLOW")
    print("-" * 60)
    
    print("\n1. Login attempt:")
    if tester.login("admin@example.com", "password123"):
        
        print("\n2. Get protected endpoint (logs):")
        tester.get("/api/v1/log")
        
        print("\n3. Get departments with auth:")
        tester.get("/api/v1/department")
    
    # Test 4: CRUD operations
    print("\n\n📌 TEST 4: CRUD OPERATIONS")
    print("-" * 60)
    
    if tester.token:
        print("\n1. Create new category:")
        tester.post("/api/v1/category", {
            "name": "Test Category",
            "priority_order": 5
        })
        
        print("\n2. Update system settings:")
        tester.patch("/api/v1/settings", {
            "quantity_formula": "(actual/target)*5"
        })
        
        print("\n3. Reset period:")
        tester.patch("/api/v1/settings/reset", {})
    
    print("\n\n" + "="*60)
    print("✅ TESTING COMPLETE")
    print("="*60 + "\n")


if __name__ == "__main__":
    # Make sure backend is running on http://localhost:5000
    print("\n⚠️  Make sure your Flask backend is running!")
    print("   Run: python backend/application.py\n")
    
    try:
        requests.get(BASE_URL, timeout=2)
        run_tests()
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to {BASE_URL}")
        print("   Start your backend server first!")
