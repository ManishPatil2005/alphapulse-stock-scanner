import urllib.request, json, time

time.sleep(1)

def get(url):
    req = urllib.request.Request(url, method='GET')
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        return {'error': str(e)}

print('--- Testing Sector Heatmap API ---')
res = get('http://127.0.0.1:8000/api/heatmap/sectors')
if 'heatmap' in res:
    root = res['heatmap']
    print(f"Root: {root['name']}")
    for sector in root['children'][:3]:
        print(f"  Sector: {sector['name']} | Change: {sector['change']}% | Market Cap: {sector['market_cap']}")

print('\n--- Testing Market Breadth API ---')
res = get('http://127.0.0.1:8000/api/heatmap/breadth')
if 'breadth' in res:
    b = res['breadth']
    print(f"Market State: {b['market_state']}")
    print(f"A/D Ratio: {b['advance_decline']['ratio']}")
    print(f"% Above 50 EMA: {b['ema_breadth']['pct_above_50']}%")

print('\n--- Testing Institutional Rotation API ---')
res = get('http://127.0.0.1:8000/api/heatmap/rotation')
if 'rotation' in res:
    r = res['rotation']
    print(f"Flow Vector: {r['rotation_vector']}")
    print(f"Top Sector: {r['top_sectors'][0]['name']} ({r['top_sectors'][0]['change']}%)")
