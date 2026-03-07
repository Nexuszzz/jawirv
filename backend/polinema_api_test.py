"""
Polinema API Testing & Integration Script
Tests various authentication methods and endpoints
"""

import requests
from requests.auth import HTTPBasicAuth
import json
from typing import Dict, Any, Optional
import time

# Configuration
NIM = "244101060077"
PASSWORD = "Fahri080506!"
API_BASE = "https://api.polinema.ac.id"

class PolinemaAPITester:
    def __init__(self, nim: str, password: str):
        self.nim = nim
        self.password = password
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        })
    
    def test_basic_auth(self, endpoint: str) -> Dict[str, Any]:
        """Test HTTP Basic Authentication"""
        print(f"\n[TEST] Basic Auth: {endpoint}")
        try:
            response = self.session.get(
                f"{API_BASE}{endpoint}",
                auth=HTTPBasicAuth(self.nim, self.password),
                timeout=30
            )
            print(f"Status: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            print(f"Response: {response.text[:500]}")
            return {"success": response.status_code == 200, "data": response.json()}
        except Exception as e:
            print(f"Error: {e}")
            return {"success": False, "error": str(e)}
    
    def test_login_endpoint(self) -> Dict[str, Any]:
        """Test POST login endpoint"""
        print(f"\n[TEST] POST Login Endpoint")
        endpoint = f"{API_BASE}/siakad/biodata/login"
        
        # Try different parameter combinations
        attempts = [
            {"nim": self.nim, "password": self.password, "showresponse": "true"},
            {"nim": self.nim, "password": self.password},
            {"username": self.nim, "password": self.password},
        ]
        
        for idx, data in enumerate(attempts, 1):
            print(f"\n  Attempt {idx}: {list(data.keys())}")
            try:
                response = self.session.post(
                    endpoint,
                    data=data,
                    timeout=30
                )
                print(f"  Status: {response.status_code}")
                print(f"  Response: {response.text[:300]}")
                
                if response.status_code == 200:
                    result = response.json()
                    # Check for token in response
                    if isinstance(result, dict):
                        for key in ['token', 'access_token', 'session', 'data']:
                            if key in result:
                                print(f"  ✓ Found key: {key}")
                                return {"success": True, "data": result}
                    
                # Check cookies
                if response.cookies:
                    print(f"  Cookies: {dict(response.cookies)}")
                    return {"success": True, "data": result, "cookies": dict(response.cookies)}
                    
            except Exception as e:
                print(f"  Error: {e}")
        
        return {"success": False, "error": "All login attempts failed"}
    
    def test_endpoints_with_session(self, cookies: Optional[Dict] = None) -> Dict[str, Any]:
        """Test various endpoints using session/cookies"""
        print(f"\n[TEST] Testing endpoints with session")
        
        if cookies:
            self.session.cookies.update(cookies)
        
        endpoints = [
            "/siakad/biodata/mahasiswa?nim=" + self.nim,
            "/siakad/biodata/akademik?nim=" + self.nim,
            "/siakad/master/kalender?tahun=2025&awal=2025-01-01&akhir=2025-12-31",
            "/siakad/master/semester",
        ]
        
        results = {}
        for endpoint in endpoints:
            print(f"\n  Testing: {endpoint}")
            try:
                response = self.session.get(f"{API_BASE}{endpoint}", timeout=30)
                print(f"  Status: {response.status_code}")
                results[endpoint] = {
                    "status": response.status_code,
                    "response": response.text[:200]
                }
                if response.status_code == 200:
                    print(f"  ✓ SUCCESS!")
                    print(f"  Data: {response.text[:300]}")
            except Exception as e:
                print(f"  Error: {e}")
                results[endpoint] = {"error": str(e)}
        
        return results
    
    def test_siakad_web_session(self) -> Dict[str, Any]:
        """Try to login to SIAKAD web and extract session"""
        print(f"\n[TEST] SIAKAD Web Login")
        
        try:
            # Get login page first
            login_page = self.session.get("https://siakad.polinema.ac.id/", timeout=30)
            print(f"Login page status: {login_page.status_code}")
            
            # Try to find login endpoint by examining the page
            if 'form' in login_page.text.lower():
                print("Found login form, analyzing...")
                # Common SIAKAD login patterns
                login_attempts = [
                    {
                        "url": "https://siakad.polinema.ac.id/login",
                        "data": {"username": self.nim, "password": self.password}
                    },
                    {
                        "url": "https://siakad.polinema.ac.id/auth/login",
                        "data": {"nim": self.nim, "password": self.password}
                    },
                ]
                
                for attempt in login_attempts:
                    print(f"\n  Trying: {attempt['url']}")
                    try:
                        response = self.session.post(
                            attempt['url'],
                            data=attempt['data'],
                            timeout=30,
                            allow_redirects=True
                        )
                        print(f"  Status: {response.status_code}")
                        print(f"  Cookies: {dict(self.session.cookies)}")
                        
                        if response.status_code == 200 and 'dashboard' in response.url.lower():
                            print("  ✓ Login successful!")
                            return {"success": True, "cookies": dict(self.session.cookies)}
                    except Exception as e:
                        print(f"  Error: {e}")
            
            return {"success": False, "error": "Could not login to SIAKAD web"}
            
        except Exception as e:
            print(f"Error: {e}")
            return {"success": False, "error": str(e)}

def main():
    print("="*60)
    print("POLINEMA API INTEGRATION TESTER")
    print("="*60)
    
    tester = PolinemaAPITester(NIM, PASSWORD)
    
    # Test 1: Basic Auth on various endpoints
    print("\n\n### TEST 1: HTTP Basic Authentication ###")
    tester.test_basic_auth("/siakad/biodata/mahasiswa?nim=" + NIM)
    tester.test_basic_auth("/siakad/master/semester")
    
    # Test 2: Login endpoint
    print("\n\n### TEST 2: Login Endpoint ###")
    login_result = tester.test_login_endpoint()
    
    # Test 3: If login successful, test other endpoints
    if login_result.get("success"):
        print("\n\n### TEST 3: Using Login Session ###")
        cookies = login_result.get("cookies")
        tester.test_endpoints_with_session(cookies)
    
    # Test 4: SIAKAD Web Login
    print("\n\n### TEST 4: SIAKAD Web Login ###")
    web_result = tester.test_siakad_web_session()
    
    if web_result.get("success"):
        print("\n\n### TEST 5: Using Web Session ###")
        tester.test_endpoints_with_session()
    
    print("\n\n" + "="*60)
    print("Testing Complete!")
    print("="*60)

if __name__ == "__main__":
    main()
