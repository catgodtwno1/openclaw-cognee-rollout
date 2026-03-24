#!/usr/bin/env python3
import argparse, json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--config', default=str(Path.home()/'.openclaw'/'openclaw.json'))
parser.add_argument('--base-url', required=True)
parser.add_argument('--dataset-name', required=True)
parser.add_argument('--search-type', default='CHUNKS')
args = parser.parse_args()

p = Path(args.config)
data = json.loads(p.read_text())
plugins = data.setdefault('plugins', {})
entries = plugins.setdefault('entries', {})
cfg = entries.setdefault('cognee-openclaw', {}).setdefault('config', {})
plugins.setdefault('slots', {})['memory'] = 'cognee-openclaw'
entries.setdefault('memory-core', {})['enabled'] = False
entries.setdefault('memory-lancedb', {})['enabled'] = False
entries.setdefault('cognee-openclaw', {})['enabled'] = True

cfg.update({
    'baseUrl': args.base_url,
    'datasetName': args.dataset_name,
    'searchType': args.search_type,
    'autoRecall': True,
    'autoIndex': True,
    'autoCognify': True,
    'deleteMode': 'soft',
    'maxResults': 6,
    'maxTokens': 512,
    'requestTimeoutMs': 60000,
    'ingestionTimeoutMs': 300000,
})

p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
print(f'Updated {p}')
print(json.dumps(cfg, ensure_ascii=False, indent=2))
