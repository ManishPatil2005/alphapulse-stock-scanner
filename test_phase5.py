import urllib.request, json, time
from datetime import datetime, timedelta

time.sleep(1)

print('--- Testing Learning Modules API ---')
url_edu = 'http://127.0.0.1:8000/api/learning/modules'
req_edu = urllib.request.Request(url_edu, method='GET')
try:
    with urllib.request.urlopen(req_edu) as response:
        res = json.loads(response.read().decode())
        print('Fetched modules:', len(res['modules']))
        print('First module:', res['modules'][0]['title'])
except Exception as e:
    print('Failed:', e)

print('\n--- Testing Psychology Cockpit API ---')
now = datetime.utcnow()
trades = [
    {
        'id': 'T1', 'symbol': 'NVDA', 'direction': 'LONG', 
        'entry_price': 100, 'exit_price': 90, 'pnl': -1000, 
        'capital_risked': 1000, 'account_value': 100000,
        'timestamp': (now - timedelta(minutes=15)).isoformat()
    },
    {
        'id': 'T2', 'symbol': 'NVDA', 'direction': 'LONG', 
        'entry_price': 95, 'exit_price': 85, 'pnl': -1000, 
        'capital_risked': 6000, 'account_value': 99000,
        'timestamp': (now - timedelta(minutes=10)).isoformat()
    }
]

mods = [
    {
        'trade_id': 'T1', 'direction': 'LONG',
        'old_stop': 95, 'new_stop': 80,
        'entry_price': 100,
        'timestamp': (now - timedelta(minutes=14)).isoformat()
    }
]

url_psy = 'http://127.0.0.1:8000/api/psychology/analyze'
data = {'trades': trades, 'order_modifications': mods}
req_psy = urllib.request.Request(url_psy, method='POST', headers={'Content-Type': 'application/json'}, data=json.dumps(data).encode())
try:
    with urllib.request.urlopen(req_psy) as response:
        res = json.loads(response.read().decode())
        analysis = res['analysis']
        print('Psychology Score:', analysis['psychology_score'])
        print('Summary:', analysis['summary'])
        print('Flags:')
        for f in analysis['flags']:
            print(f"  [{f['severity']}] {f['type']}: {f['message']}")
except Exception as e:
    print('Failed:', e)
