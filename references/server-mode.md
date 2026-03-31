# Server mode (updated 2026-03-31)

Use this when one Mac mini hosts Cognee for other OpenClaw clients.

## 1. Docker (native on Mac)

macOS uses Docker Desktop or OrbStack natively. Colima is no longer required.

## 2. Secrets

Store API keys in `~/.openclaw/cognee/.env`:

```dotenv
LLM_API_KEY=sk-cp-...
EMBEDDING_API_KEY=sk-...
```

Do not store secrets in the skill.

## 3. Run Cognee on LAN (0.0.0.0)

⚠️ **Critical:** Bind to `0.0.0.0:8000`, not `127.0.0.1:8000`. Other machines cannot connect to localhost-bound containers.

```bash
docker rm -f cognee >/dev/null 2>&1 || true

docker run -d --name cognee --restart unless-stopped \
  --add-host=host.docker.internal:host-gateway \
  --env-file ~/.openclaw/cognee/.env \
  -p 0.0.0.0:8000:8000 \
  -e COGNEE_SKIP_CONNECTION_TEST=true \
  -e LLM_PROVIDER=custom \
  -e LLM_MODEL=openai/MiniMax-M2.7-highspeed \
  -e LLM_ENDPOINT=https://api.minimaxi.com/v1 \
  -e LLM_INSTRUCTOR_MODE=json_mode \
  -e LLM_MAX_COMPLETION_TOKENS=8192 \
  -e 'LLM_ARGS={"max_tokens":8192,"timeout":120}' \
  -e EMBEDDING_PROVIDER=custom \
  -e EMBEDDING_MODEL=openai/BAAI/bge-m3 \
  -e EMBEDDING_ENDPOINT=https://api.siliconflow.cn/v1 \
  -e EMBEDDING_DIMENSIONS=1024 \
  -e STRUCTURED_OUTPUT_FRAMEWORK=instructor \
  -e LITELLM_DROP_PARAMS=true \
  -e LITELLM_REQUEST_TIMEOUT=120 \
  -e REQUIRE_AUTHENTICATION=false \
  -e ENABLE_BACKEND_ACCESS_CONTROL=false \
  -e LOG_LEVEL=DEBUG \
  -e PYTHONUNBUFFERED=1 \
  cognee-fixed:v5
```

**Image note:** `cognee-fixed:v5` is a patched build of `cognee/cognee:latest` with two fixes:
1. Message role order (MiniMax requires system at position 0)
2. Embedding dimensions removal (SiliconFlow bge-m3 rejects dimensions=3072)

See `validated-config.md` for patch details.

## 4. Verify

```bash
# Health check
curl http://HOST_IP:8000/health
# Expected: {"status":"ready","health":"healthy","version":"0.5.6-local"}

# Check port binding
docker port cognee
# Expected: 8000/tcp -> 0.0.0.0:8000
# ❌ If shows 127.0.0.1:8000 → other machines can't connect!

# Test from another machine
ssh scott@OTHER_IP "curl -s http://HOST_IP:8000/health"
```

## 5. End-to-end pipeline test

```bash
# Add test data
echo "OpenClaw test memory entry" > /tmp/cognee_test.txt
curl -s -X POST 'http://HOST_IP:8000/api/v1/add' \
  -F "data=@/tmp/cognee_test.txt;type=text/plain" \
  -F "datasetName=openclaw-main-v7"

# Cognify
curl -s -X POST 'http://HOST_IP:8000/api/v1/cognify' \
  -H 'Content-Type: application/json' \
  -d '{"datasets":["openclaw-main-v7"]}'

# Search (after cognify completes)
curl -s -X POST 'http://HOST_IP:8000/api/v1/search' \
  -H 'Content-Type: application/json' \
  -d '{"query":"OpenClaw test","searchType":"CHUNKS"}'
```

## 6. Network access for other Mac minis

### LAN
- Use `http://HOST_IP:8000`
- Ensure macOS firewall allows inbound 8000 if enabled

### Tailnet / VPN
- Prefer a stable tailnet IP or DNS name

### Public exposure
Not recommended. Use private network or tunnel with access control.

## 7. Dataset strategy

Use a shared dataset for the same user's machines:

- `openclaw-main-v7` — unified dataset for all 4 Mac minis

Individual datasets only if explicit isolation is needed.

## 8. Common pitfall: container rebuild loses data

Cognee stores data in internal SQLite. Rebuilding the container (docker rm + run) resets all datasets.

**Mitigation options:**
- Mount a volume: `-v cognee_data:/app/cognee/.cognee_system`
- Accept rebuild: data will re-accumulate from OpenClaw usage
- NAS backup: keep a NAS Cognee as cold backup with imported data
