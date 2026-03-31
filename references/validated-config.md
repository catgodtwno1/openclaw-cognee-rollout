# Validated config (updated 2026-03-31)

## OpenClaw plugin config snippet

```json
{
  "baseUrl": "http://SERVER_IP:8000",
  "datasetName": "openclaw-main-v7",
  "searchType": "CHUNKS",
  "autoRecall": false,
  "autoIndex": true,
  "autoCognify": true,
  "deleteMode": "soft",
  "maxResults": 3,
  "maxTokens": 512,
  "requestTimeoutMs": 60000,
  "ingestionTimeoutMs": 300000
}
```

**Note:** `autoRecall: false` because `memory-lancedb-pro` owns the primary memory slot.

## Canonical container env (cognee-fixed:v5)

```text
COGNEE_SKIP_CONNECTION_TEST=true
LLM_PROVIDER=custom
LLM_MODEL=openai/MiniMax-M2.7-highspeed
LLM_ENDPOINT=https://api.minimaxi.com/v1
LLM_INSTRUCTOR_MODE=json_mode
LLM_MAX_COMPLETION_TOKENS=8192
LLM_ARGS={"max_tokens":8192,"timeout":120}
EMBEDDING_PROVIDER=custom
EMBEDDING_MODEL=openai/BAAI/bge-m3
EMBEDDING_ENDPOINT=https://api.siliconflow.cn/v1
EMBEDDING_DIMENSIONS=1024
STRUCTURED_OUTPUT_FRAMEWORK=instructor
LITELLM_DROP_PARAMS=true
LITELLM_REQUEST_TIMEOUT=120
REQUIRE_AUTHENTICATION=false
ENABLE_BACKEND_ACCESS_CONTROL=false
LOG_LEVEL=DEBUG
PYTHONUNBUFFERED=1
```

### LLM Model Selection History

| Model | KG Extraction | Issue |
|-------|--------------|-------|
| SiliconFlow Qwen2.5-32B | ❌ TPM rate limit | Free tier too restrictive for batch cognify |
| MiniMax M2.1-HS | ❌ thinking overflow | All tokens consumed by `<think>` tags, zero JSON output |
| MiniMax M2.5-HS | ✅ Works | Stable JSON output, but nondeterministic on edge cases |
| **MiniMax M2.7-HS** | ✅ **Best** | Requires `max_tokens≥8192` to accommodate reasoning_tokens + output |

### M2.7-HS Reasoning Token Behavior

M2.7-HS is a reasoning model (like DeepSeek R1). Key facts:
- Reasoning tokens consume the `max_tokens` budget (not separate)
- KG extraction uses ~3000-4000 reasoning tokens, needs ~3000+ for JSON output
- **At `max_tokens=4096`**: frequent truncation (finish_reason=length, no JSON)
- **At `max_tokens=8192`**: 100% success rate (12/12 in benchmark)
- `thinking.enabled=false` only budgets reasoning allocation (~110 tokens), does NOT suppress `<think>` tags
- No API parameter can fully disable thinking — increase max_tokens instead

## Docker image: cognee-fixed:v5

Built from `cognee/cognee:latest` with two patches:

### PATCH1: Message role order fix
Cognee sends `[user, system]` message order; MiniMax requires system at position 0.
Files patched: `azure_openai/adapter.py`, `gemini/adapter.py`, `openai/adapter.py`, `generic_llm_api/adapter.py`

### PATCH2: Embedding dimensions removal
SiliconFlow BAAI/bge-m3 rejects `dimensions=3072` parameter (HTTP 422).
`LITELLM_DROP_PARAMS=true` alone is insufficient — manually removed dimensions kwarg in `LiteLLMEmbeddingEngine`.

## Validation target

A rollout is only considered complete when all of these are true:

- `/health` returns `{"status":"ready","health":"healthy"}`
- add → cognify → search pipeline works end-to-end
- Search returns real memory content (not just health check)
- Port binding is `0.0.0.0:8000` (not `127.0.0.1`) when serving other machines
