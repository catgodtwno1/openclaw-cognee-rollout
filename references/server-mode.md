# Server mode

Use this when one Mac mini hosts Cognee for other OpenClaw clients.

## 1. Start Docker/Colima

If using Colima:

```bash
colima start
export DOCKER_HOST=unix:///Users/scott/.colima/default/docker.sock
```

## 2. Minimal `.env`

Create `~/.openclaw/cognee/.env` with only secrets:

```dotenv
SILICONFLOW_API_KEY=...
LLM_API_KEY=...
EMBEDDING_API_KEY=...
```

Do not store secrets in the skill.

## 3. Run Cognee on the host LAN IP

Example:

```bash
docker rm -f cognee >/dev/null 2>&1 || true

docker run -d --name cognee --restart unless-stopped \
  --env-file ~/.openclaw/cognee/.env \
  -e LOG_LEVEL=INFO \
  -e COGNEE_SKIP_CONNECTION_TEST=true \
  -e HUGGINGFACE_TOKENIZER='BAAI/bge-m3' \
  -e LLM_PROVIDER=openai \
  -e LLM_MODEL='openai/Qwen/Qwen2.5-72B-Instruct' \
  -e LLM_ENDPOINT='https://api.siliconflow.cn/v1' \
  -e LLM_INSTRUCTOR_MODE=json_mode \
  -e EMBEDDING_PROVIDER=custom \
  -e EMBEDDING_MODEL='openai/BAAI/bge-m3' \
  -e EMBEDDING_ENDPOINT='https://api.siliconflow.cn/v1' \
  -e STRUCTURED_OUTPUT_FRAMEWORK=instructor \
  -e LITELLM_DROP_PARAMS=true \
  -p 0.0.0.0:8000:8000 \
  -v cognee_data:/app/cognee/.cognee_system \
  cognee/cognee:latest
```

## 4. Apply hotfixes

```bash
bash skills/openclaw-cognee-rollout/scripts/apply_cognee_hotfix.sh
```

## 5. Verify

```bash
curl http://HOST_IP:8000/health
```

## 6. Network access for other Mac minis

### LAN
- use `http://HOST_IP:8000`
- ensure macOS firewall allows inbound 8000 if enabled

### Tailnet / VPN
- prefer a stable tailnet IP or DNS name
- clients should use `http://TAILNET_IP:8000`

### Public exposure
Not recommended raw. Put it behind a private network, reverse proxy, or tunnel with access control.

## 7. Dataset strategy

Prefer one dataset per client machine at first:

- `openclaw-main-laoda`
- `openclaw-main-laoer`
- `openclaw-main-laosan`
- `openclaw-main-laosi`

Only share one dataset if the user explicitly wants a common memory pool.
