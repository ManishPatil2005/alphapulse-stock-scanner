"""
test_hosted_api.py
Tests all API endpoints directly on https://alphapulse-stock-scanner.vercel.app
"""

import sys
import json
import urllib.request
import urllib.parse

sys.stdout.reconfigure(encoding="utf-8")
base = "https://alphapulse-stock-scanner.vercel.app"

print("======================================================================")
print(f"  TESTING LIVE HOSTED API ENDPOINTS ON {base}")
print("======================================================================")

endpoints = [
    ("GET /api/universes", f"{base}/api/universes", "GET", None),
    ("GET /api/sectors", f"{base}/api/sectors", "GET", None),
    ("GET /api/search?q=rel", f"{base}/api/search?q=rel", "GET", None),
    ("GET /api/search?q=apple", f"{base}/api/search?q=apple", "GET", None),
    ("GET /api/chart/NVDA", f"{base}/api/chart/NVDA?timeframe=1d&range_param=3mo", "GET", None),
    ("GET /api/chart/RELIANCE.NS", f"{base}/api/chart/RELIANCE.NS?timeframe=1d&range_param=3mo", "GET", None),
    ("GET /api/quick-quote/NVDA", f"{base}/api/quick-quote/NVDA", "GET", None),
    ("POST /api/backtest", f"{base}/api/backtest", "POST", {
        "symbol": "NVDA",
        "timeframe": "1d",
        "data_range": "1y",
        "strategy": "master",
        "risk_reward": 2.0,
        "initial_capital": 100000.0,
        "risk_per_trade_pct": 1.0
    }),
    ("POST /api/scan", f"{base}/api/scan", "POST", {
        "universe": "us_mega_caps",
        "timeframe": "1d",
        "filter_circuits": True,
        "require_episodic_pivot": False,
        "require_liquidity_sweep": False
    })
]

for label, url, method, payload in endpoints:
    try:
        data_bytes = json.dumps(payload).encode("utf-8") if payload else None
        headers = {"User-Agent": "Mozilla/5.0"}
        if data_bytes:
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read()
            data = json.loads(content.decode("utf-8"))
            print(f"  [✓] {label:30} -> HTTP {resp.status} | Payload size: {len(content)} bytes")
    except Exception as e:
        print(f"  [X] {label:30} -> FAILED: {e}")

print("\nFinished hosted API checks.")
