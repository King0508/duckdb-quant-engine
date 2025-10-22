"""Test API endpoints after database regeneration."""
import requests
import time
import sys

# Wait for API to start
print("Waiting for API to start...")
time.sleep(4)

base_url = "http://localhost:8000"

endpoints = [
    ("/", "Root endpoint"),
    ("/treasury/yields/latest", "Latest Treasury yields"),
    ("/treasury/etfs/latest", "Latest ETF prices"),
    ("/treasury/summary", "Treasury summary"),
    ("/sentiment/news/recent?hours=168&limit=10", "Recent news (7 days)"),
]

print("\n=== TESTING API ENDPOINTS ===\n")

all_passed = True
for endpoint, description in endpoints:
    try:
        response = requests.get(f"{base_url}{endpoint}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            count = len(data) if isinstance(data, list) else "OK"
            print(f"[OK] {endpoint}")
            print(f"     {description}: {count}")
        else:
            print(f"[FAIL] {endpoint} - Status {response.status_code}")
            print(f"       {response.text[:200]}")
            all_passed = False
    except requests.exceptions.ConnectionError:
        print(f"[ERROR] {endpoint} - API not responding")
        all_passed = False
    except Exception as e:
        print(f"[ERROR] {endpoint} - {str(e)[:100]}")
        all_passed = False

print("\n=== RESULT ===")
if all_passed:
    print("[SUCCESS] All endpoints working!")
    sys.exit(0)
else:
    print("[FAILED] Some endpoints failed")
    sys.exit(1)

