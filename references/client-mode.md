# Client mode

Use this on any Mac mini that should consume a shared Cognee service.

## Fast path: generic onboarding script

Use the generic onboarding script when you want a reusable method that does not depend on any specific machine name.

```bash
bash skills/openclaw-cognee-rollout/scripts/onboard_cognee_client.sh \
  --base-url http://SERVER_IP:8000
```

Default behavior:
- patch local `cognee-openclaw`
- update `~/.openclaw/openclaw.json`
- reset local Cognee sync state
- run `openclaw cognee index`
- run smoke test
- generate dataset name automatically as `openclaw-<normalized-hostname>`

Use `--dataset-name NAME` if you want to override it.

## Manual path

### 1. Patch the local plugin

```bash
python3 skills/openclaw-cognee-rollout/scripts/patch_openclaw_cognee_plugin.py
```

### 2. Point OpenClaw at the remote server

```bash
python3 skills/openclaw-cognee-rollout/scripts/configure_openclaw_cognee_client.py \
  --base-url http://SERVER_IP:8000 \
  --dataset-name openclaw-client-name \
  --search-type CHUNKS
```

This updates `~/.openclaw/openclaw.json`.

### 3. Reset local Cognee sync state when switching datasets

```bash
printf '{}' > ~/.openclaw/memory/cognee/datasets.json
printf '{"entries":{}}' > ~/.openclaw/memory/cognee/sync-index.json
```

### 4. Re-index

```bash
openclaw cognee index
```

### 5. Verify

```bash
openclaw cognee health
openclaw cognee status
python3 skills/openclaw-cognee-rollout/scripts/cognee_smoke_test.py --base-url http://SERVER_IP:8000
```

## Notes

- Use a unique dataset per machine unless the user explicitly wants pooled memory.
- `searchType=CHUNKS` is the stable default during rollout.
- If a dataset gets stuck in `ERRORED`, do not keep hammering it; switch to a fresh dataset name.
