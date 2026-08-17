"""
scripts/test_api.py
Run after the server is started: python -m scripts.test_api
Tests all endpoints against the current binary failure model API.
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


def post_expect_error(path, body):
    data = json.dumps(body).encode()
    req = urllib.request.Request(f"{BASE}{path}", data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def check(label, status, body, expected_status=200, required_keys=()):
    ok = status == expected_status and all(k in body for k in required_keys)
    icon = PASS if ok else FAIL
    print(f"{icon}  [{status}] {label}")
    if not ok:
        print(f"       body: {json.dumps(body, indent=2)[:400]}")
    else:
        preview = json.dumps(body)[:120]
        print(f"       {preview}")
    return ok


results = []

# 1. Health
try:
    s, b = get("/health")
    results.append(check(
        "GET /health", s, b,
        required_keys=["status", "db", "model", "pipeline"]
    ))
except Exception as e:
    print(f"{FAIL}  GET /health — {e}"); results.append(False)

# 2. Metrics
try:
    s, b = get("/metrics")
    results.append(check(
        "GET /metrics", s, b,
        required_keys=["roc_auc", "f1_tuned", "f1_default", "threshold"]
    ))
except urllib.error.HTTPError as e:
    if e.code == 404:
        print(f"\033[93m SKIP\033[0m  GET /metrics — 404 (run seed_db.py first)")
        results.append(True)
    else:
        print(f"{FAIL}  GET /metrics — {e}"); results.append(False)
except Exception as e:
    print(f"{FAIL}  GET /metrics — {e}"); results.append(False)

# 3. Metrics/all
try:
    s, b = get("/metrics/all")
    ok = s == 200 and isinstance(b, list)
    print(f"{PASS if ok else FAIL}  [200] GET /metrics/all — {len(b)} version(s)")
    results.append(ok)
except Exception as e:
    print(f"{FAIL}  GET /metrics/all — {e}"); results.append(False)

# 4. Manufacturers autocomplete
try:
    s, b = get("/manufacturers?q=medtronic&limit=5")
    ok = s == 200 and isinstance(b, list) and len(b) > 0
    print(f"{PASS if ok else FAIL}  [200] GET /manufacturers?q=medtronic — {len(b)} results")
    results.append(ok)
except Exception as e:
    print(f"{FAIL}  GET /manufacturers — {e}"); results.append(False)

# 5. Predict — with manufacturer
try:
    s, b = post("/predict", {
        "description": "Implantable cardiac defibrillator for ventricular arrhythmia management",
        "classification": "Cardiovascular Devices",
        "manufacturer_name": "Medtronic"
    })
    results.append(check(
        "POST /predict (with manufacturer)", s, b,
        required_keys=["predicted_failure", "predicted_label", "confidence",
                       "low_confidence_flag", "prob_failure", "prob_no_failure",
                       "top_features", "escalated"]
    ))
except Exception as e:
    print(f"{FAIL}  POST /predict (with manufacturer) — {e}"); results.append(False)

# 6. Predict — no manufacturer
try:
    s, b = post("/predict", {
        "description": "Sterile adhesive bandage for wound closure",
        "classification": "General Hospital Devices",
    })
    results.append(check(
        "POST /predict (no manufacturer)", s, b,
        required_keys=["predicted_failure", "confidence", "prob_failure", "escalated"]
    ))
except Exception as e:
    print(f"{FAIL}  POST /predict (no manufacturer) — {e}"); results.append(False)

# 7. Predict — with known_prior_incidents (escalation rule)
try:
    s, b = post("/predict", {
        "description": "Implantable cardiac defibrillator for ventricular arrhythmia management",
        "classification": "Cardiovascular Devices",
        "manufacturer_name": "Medtronic",
        "known_prior_incidents": 3
    })
    ok = s == 200 and "escalated" in b
    print(f"{PASS if ok else FAIL}  [200] POST /predict (with known_prior_incidents=3) — escalated={b.get('escalated')}")
    results.append(ok)
except Exception as e:
    print(f"{FAIL}  POST /predict (escalation) — {e}"); results.append(False)

# 8. Predict — validation error (short description)
try:
    s, b = post_expect_error("/predict", {
        "description": "hi",
        "classification": "Cardiovascular Devices"
    })
    ok = s == 422
    print(f"{PASS if ok else FAIL}  [422] POST /predict (short description) — got {s}")
    results.append(ok)
except Exception as e:
    print(f"{FAIL}  POST /predict (validation) — {e}"); results.append(False)

# 9. Predict — missing description
try:
    s, b = post_expect_error("/predict", {"classification": "Cardiovascular Devices"})
    ok = s == 422
    print(f"{PASS if ok else FAIL}  [422] POST /predict (missing description) — got {s}")
    results.append(ok)
except Exception as e:
    print(f"{FAIL}  POST /predict (missing field) — {e}"); results.append(False)

# 10. History
try:
    s, b = get("/predictions?limit=5")
    ok = s == 200 and isinstance(b, list)
    print(f"{PASS if ok else FAIL}  [200] GET /predictions — {len(b)} records")
    results.append(ok)
except Exception as e:
    print(f"{FAIL}  GET /predictions — {e}"); results.append(False)

# 11. History pagination
try:
    s, b = get("/predictions?skip=0&limit=2")
    ok = s == 200 and isinstance(b, list) and len(b) <= 2
    print(f"{PASS if ok else FAIL}  [200] GET /predictions?skip=0&limit=2 — {len(b)} records")
    results.append(ok)
except Exception as e:
    print(f"{FAIL}  GET /predictions (pagination) — {e}"); results.append(False)

print(f"\n{'='*40}")
passed = sum(results)
total = len(results)
print(f"  {passed}/{total} tests passed")
if passed < total:
    sys.exit(1)
