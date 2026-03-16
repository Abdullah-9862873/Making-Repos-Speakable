#!/usr/bin/env python3
# =============================================================================
# AI Multimodal Tutor - Integration Test Script
# =============================================================================
# Phase: 7 - Integration & Testing
# Purpose: Test all API endpoints
# Version: 7.0.0
# =============================================================================

import requests
import time
import sys
import json
import os

# Fix Unicode on Windows
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# Configuration
BASE_URL = "http://localhost:8000"

# Colors for terminal output (ASCII-safe)
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

# ASCII-safe checkmarks
CHECK = '[OK]'
CROSS = '[FAIL]'

def print_test(name, status, message=""):
    """Print test result"""
    if status:
        print(f"{GREEN}{CHECK}{RESET} {name}")
    else:
        print(f"{RED}{CROSS}{RESET} {name}")
        if message:
            print(f"  {RED}Error: {message}{RESET}")

def test_health():
    """Test health endpoint"""
    print(f"\n{BLUE}Testing Health Endpoint...{RESET}")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        data = response.json()
        
        if response.status_code == 200 and data.get("status") == "healthy":
            print_test("Health check", True)
            return True
        else:
            print_test("Health check", False, f"Status: {response.status_code}")
            return False
    except Exception as e:
        print_test("Health check", False, str(e))
        return False

def test_validate_repo_valid():
    """Test validate repo with valid public repo"""
    print(f"\n{BLUE}Testing Validate Repo (Valid)...{RESET}")
    try:
        response = requests.post(
            f"{BASE_URL}/validate-repo",
            json={"repo": "microsoft/vscode"},
            timeout=10
        )
        data = response.json()
        
        if response.status_code == 200 and data.get("is_public") == True:
            print_test("Validate public repo (microsoft/vscode)", True)
            return True
        else:
            print_test("Validate public repo", False, f"Status: {response.status_code}")
            return False
    except Exception as e:
        print_test("Validate public repo", False, str(e))
        return False

def test_validate_repo_invalid():
    """Test validate repo with invalid repo"""
    print(f"\n{BLUE}Testing Validate Repo (Invalid)...{RESET}")
    try:
        response = requests.post(
            f"{BASE_URL}/validate-repo",
            json={"repo": "invalid/nonexistent-repo-12345"},
            timeout=10
        )
        data = response.json()
        
        if response.status_code == 200 and data.get("valid") == False:
            print_test("Validate invalid repo", True)
            return True
        else:
            print_test("Validate invalid repo", False, f"Status: {response.status_code}")
            return False
    except Exception as e:
        print_test("Validate invalid repo", False, str(e))
        return False

def test_validate_repo_url_format():
    """Test validate repo with full URL format"""
    print(f"\n{BLUE}Testing Validate Repo (Full URL)...{RESET}")
    try:
        response = requests.post(
            f"{BASE_URL}/validate-repo",
            json={"repo": "https://github.com/microsoft/vscode"},
            timeout=10
        )
        data = response.json()
        
        if response.status_code == 200 and data.get("is_public") == True:
            print_test("Validate repo with full URL", True)
            return True
        else:
            print_test("Validate repo with full URL", False, f"Status: {response.status_code}")
            return False
    except Exception as e:
        print_test("Validate repo with full URL", False, str(e))
        return False

def test_ingest_status():
    """Test ingest status endpoint"""
    print(f"\n{BLUE}Testing Ingest Status...{RESET}")
    try:
        response = requests.get(f"{BASE_URL}/ingest/status", timeout=30)
        data = response.json()
        
        if response.status_code == 200 and "total_vectors" in data:
            print_test("Ingest status", True, f" Vectors: {data.get('total_vectors', 0)}")
            return True
        else:
            print_test("Ingest status", False, f"Status: {response.status_code}")
            return False
    except Exception as e:
        print_test("Ingest status", False, str(e))
        return False

def test_api_root():
    """Test API root endpoint"""
    print(f"\n{BLUE}Testing API Root...{RESET}")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        data = response.json()
        
        if response.status_code == 200 and data.get("name"):
            print_test("API root", True)
            return True
        else:
            print_test("API root", False, f"Status: {response.status_code}")
            return False
    except Exception as e:
        print_test("API root", False, str(e))
        return False

def run_all_tests():
    """Run all tests"""
    print(f"\n{BLUE}{'='*50}{RESET}")
    print(f"{BLUE}AI Multimodal Tutor - Integration Tests{RESET}")
    print(f"{BLUE}{'='*50}{RESET}")
    
    results = []
    
    # Run tests
    results.append(test_api_root())
    results.append(test_health())
    results.append(test_validate_repo_valid())
    results.append(test_validate_repo_invalid())
    results.append(test_validate_repo_url_format())
    results.append(test_ingest_status())
    
    # Summary
    print(f"\n{BLUE}{'='*50}{RESET}")
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"{GREEN}All tests passed! ({passed}/{total}){RESET}")
    else:
        print(f"{YELLOW}Some tests failed! ({passed}/{total}){RESET}")
    
    print(f"{BLUE}{'='*50}{RESET}")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
