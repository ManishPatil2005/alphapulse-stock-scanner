import urllib.request, json, time

time.sleep(1)

def request_api(url, token="token_retail_123"):
    req = urllib.request.Request(url, method='GET', headers={'Authorization': f'Bearer {token}'})
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        return {'status': 'error', 'code': e.code, 'reason': e.reason}

print('--- Testing /api/auth/me (Retail User) ---')
res = request_api('http://127.0.0.1:8000/api/auth/me', token="token_retail_123")
print(res)

print('\n--- Testing /api/auth/me (Institutional User) ---')
res = request_api('http://127.0.0.1:8000/api/auth/me', token="token_inst_789")
print(res)

print('\n--- Testing /api/admin/telemetry (Retail Access) ---')
res = request_api('http://127.0.0.1:8000/api/admin/telemetry', token="token_retail_123")
print('Should be Forbidden (403):', res)

print('\n--- Testing /api/admin/telemetry (Admin Access) ---')
res = request_api('http://127.0.0.1:8000/api/admin/telemetry', token="token_admin_999")
print('Metrics:', res.get('metrics', res))
