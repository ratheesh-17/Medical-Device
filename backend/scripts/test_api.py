"""
scripts/test_api.py
Run after the server is started: python -m scripts.test_api
Tests all 5 endpoints in order.
"""

import sys
import json
import urllib.request
import urllib.error

BASE = "http://localhost:8000/api/v1"
PASS = "\033[92m PASS\033[0m"
FAIL = "\033[91m FAIL\033[0m"


def get(path):
    req = urllib.request.Request(f"{BASE}{path}")
    with urllib.request.urlopen(req, timeout=5) as r:
        return r.status, json.loads(r.read())


def post(path, body):
    data = json.dumps(body).encode()
    req = urllib.request.Request(f"{BASE}{path}", data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=5) as r:
        return r.status, json.loads(r.read())


def check(label, status, body, expected_status=200, required_keys=()):
    ok = status == expected_status and all(k in body for k in required_keys)
    icon = PASS if ok else FAIL
    print(f"{icon}  [{status}] {label}")
    if not ok:
        print(f"       body: {json.dumps(body, indent=2)[:300]}")
    else:
        print(f"       {json.dumps(body)[:120]}")
    return ok


results = []

# 1. Health
try:
    s, b = get("/health")
    results.append(check("GET /health", s, b, required_keys=["status", "db", "model", "pipeline"]))
except Exception as e:
    print(f"{FAIL}  GET /health — {e}")
    results.append(False)

# 2. Manufacturers autocomplete
try:
    s, b = get("/manufacturers?q=med&limit=5")
    results.append(check("GET /manufacturers?q=med", s, b if isinstance(b, dict) else {"items": b}, required_keys=[]))
    print(f"       returned {len(b)} items")
except Exception as e:
    print(f"{FAIL}  GET /manufacturers — {e}")
    results.append(False)

# 3. Predict — high risk device
try:
    s, b = post("/predict", {
        "description": "Implantable cardiac defibrillator for ventricular arrhythmia management",
        "classification": "Cardiovascular Devices",
        "manufacturer_name": "Medtronic"
    })
    results.append(check(
        "POST /predict (cardiac defibrillator)", s, b,
        required_keys=["predicted_class", "confidence", "low_confidence_flag", "probabilities", "top_features"]
    ))
except Exception as e:
    print(f"{FAIL}  POST /predict — {e}")
    results.append(False)

# 4. Predict — low risk device
try:
    s, b = post("/predict", {
        "description": "Sterile adhesive bandage for wound closure",
        "classification": "General Hospital and Personal Use Devices",
    })
    results.append(check(
        "POST /predict (bandage)", s, b,
        required_keys=["predicted_class", "confidence", "probabilities"]
    ))
except Exception as e:
    print(f"{FAIL}  POST /predict (bandage) — {e}")
    results.append(False)

# 5. History
try:
    s, b = get("/predictions?limit=5")
    results.append(check("GET /predictions", s, b if isinstance(b, dict) else {"items": b}))
    print(f"       returned {len(b)} records")
except Exception as e:
    print(f"{FAIL}  GET /predictions — {e}")
    results.append(False)

# 6. Metrics
try:
    s, b = get("/metrics")
    results.append(check("GET /metrics", s, b, required_keys=["version_name", "macro_f1"]))
except urllib.error.HTTPError as e:
    if e.code == 404:
        print(f"\033[93m SKIP\033[0m  GET /metrics — 404 (run seed_db.py first)")
        results.append(True)
    else:
        print(f"{FAIL}  GET /metrics — {e}")
        results.append(False)
except Exception as e:
    print(f"{FAIL}  GET /metrics — {e}")
    results.append(False)

print(f"\n{'='*40}")
passed = sum(results)
total = len(results)
print(f"  {passed}/{total} tests passed")
if passed < total:
    sys.exit(1)
