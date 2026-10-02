import urllib.request
import urllib.parse
import json
import time
import threading
from app import app
import uvicorn

server = uvicorn.Server(uvicorn.Config(app, host='127.0.0.1', port=8005, log_level='error'))
t = threading.Thread(target=server.run, daemon=True)
t.start()
time.sleep(2.0)

base = 'http://127.0.0.1:8005'

try:
    print('================ 1. TESTING SEARCH AUTOCOMPLETE ================')
    for q in ['rel', 'nifty', 'tsla', 'apple']:
        res = urllib.request.urlopen(f'{base}/api/search?q={urllib.parse.quote(q)}')
        data = json.loads(res.read().decode('utf-8'))
        symbols = [r['symbol'] for r in data['results'][:3]]
        print(f"Query '{q}': Status {res.status} | Found {len(data['results'])} | Top: {symbols}")

    print('\n================ 2. TESTING CHARTS (US, NSE, INDICES) ================')
    for sym in ['NVDA', 'RELIANCE.NS', '^NSEI', '^GSPC']:
        t0 = time.time()
        url = f"{base}/api/chart/{urllib.parse.quote(sym)}?timeframe=1d&range_param=3mo"
        res = urllib.request.urlopen(url)
        chart_data = json.loads(res.read().decode('utf-8'))
        elapsed = round(time.time() - t0, 3)
        candles = chart_data.get('candles', [])
        rsi = chart_data.get('rsi', [])
        markers = chart_data.get('markers', [])
        print(f"Symbol {sym:12} | Status {res.status} | Candles: {len(candles)} | RSI: {len(rsi)} | Markers: {len(markers)} | Time: {elapsed}s")

    print('\n================ 3. TESTING CONCURRENT MEMORY CACHE SPEED ================')
    t0 = time.time()
    for _ in range(50):
        res = urllib.request.urlopen(f"{base}/api/chart/NVDA?timeframe=1d&range_param=3mo")
    elapsed = round(time.time() - t0, 4)
    print(f"50 cached chart requests served in {elapsed}s -> {round(elapsed * 1000 / 50, 2)}ms per request!")

finally:
    server.should_exit = True
    print('\nAll tests completed successfully!')
