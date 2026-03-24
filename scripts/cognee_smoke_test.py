#!/usr/bin/env python3
import argparse, json, urllib.request, urllib.parse, subprocess
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--base-url', default='http://127.0.0.1:8000')
parser.add_argument('--dataset-name')
args = parser.parse_args()
BASE=args.base_url.rstrip('/')


def http(method, path, data=None, headers=None, timeout=60):
    hdrs=dict(headers or {})
    body=None
    if data is not None:
        if isinstance(data, dict):
            body=json.dumps(data).encode(); hdrs.setdefault('Content-Type','application/json')
        elif isinstance(data, str):
            body=data.encode()
        else:
            body=data
    req=urllib.request.Request(BASE+path, data=body, headers=hdrs, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw=r.read().decode()
        try: return r.status, json.loads(raw)
        except: return r.status, raw

# health
st, h = http('GET', '/health')
print('health:', st, h)

# login
login = urllib.parse.urlencode({'username':'default_user@example.com','password':'default_password'})
st, tok = http('POST', '/api/v1/auth/login', data=login, headers={'Content-Type':'application/x-www-form-urlencoded'})
token = tok.get('access_token') or tok.get('token')
print('login:', st, bool(token))
auth={'Authorization': f'Bearer {token}'}

# datasets
st, datasets = http('GET', '/api/v1/datasets', headers=auth)
print('datasets:', st, len(datasets) if isinstance(datasets, list) else datasets)
selected = None
if isinstance(datasets, list):
    if args.dataset_name:
        for d in datasets:
            if d.get('name') == args.dataset_name:
                selected = d
                break
    elif datasets:
        selected = datasets[-1]
if selected:
    print('selected_dataset:', json.dumps(selected, ensure_ascii=False))
    dsid = selected['id']
    st, status = http('GET', f'/api/v1/datasets/status?dataset_id={dsid}', headers=auth)
    print('dataset_status:', st, status)
    st, data_items = http('GET', f'/api/v1/datasets/{dsid}/data', headers=auth, timeout=120)
    count = len(data_items) if isinstance(data_items, list) else -1
    print('dataset_data_count:', count)
    payload = {
        'query': 'Cognee recall test',
        'searchType': 'CHUNKS',
        'datasetIds': [dsid],
        'max_tokens': 200,
    }
    try:
        st, sr = http('POST', '/api/v1/search', data=payload, headers=auth, timeout=120)
        text = json.dumps(sr, ensure_ascii=False)[:800]
        print('search:', st, text)
    except Exception as e:
        print('search_failed:', e)

# local cli status if available
try:
    p = subprocess.run(['openclaw', 'cognee', 'status'], capture_output=True, text=True, timeout=120)
    print('cli_status_exit:', p.returncode)
    print((p.stdout + p.stderr)[-500:])
except Exception as e:
    print('cli_status_failed:', e)
