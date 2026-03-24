# Validated config

## OpenClaw plugin config snippet

```json
{
  "baseUrl": "http://SERVER_IP:8000",
  "datasetName": "openclaw-main-v5",
  "searchType": "CHUNKS",
  "autoRecall": true,
  "autoIndex": true,
  "autoCognify": true,
  "deleteMode": "soft",
  "maxResults": 6,
  "maxTokens": 512,
  "requestTimeoutMs": 60000,
  "ingestionTimeoutMs": 300000
}
```

## Canonical container env

```text
COGNEE_SKIP_CONNECTION_TEST=true
HUGGINGFACE_TOKENIZER=BAAI/bge-m3
LLM_PROVIDER=openai
LLM_MODEL=openai/Qwen/Qwen2.5-72B-Instruct
LLM_ENDPOINT=https://api.siliconflow.cn/v1
LLM_INSTRUCTOR_MODE=json_mode
EMBEDDING_PROVIDER=custom
EMBEDDING_MODEL=openai/BAAI/bge-m3
EMBEDDING_ENDPOINT=https://api.siliconflow.cn/v1
STRUCTURED_OUTPUT_FRAMEWORK=instructor
LITELLM_DROP_PARAMS=true
```

## Validation target

A rollout is only considered complete when all of these are true:

- `openclaw cognee health` succeeds
- `openclaw cognee index` reports `0 errors`
- add/update/delete flows work
- a real search or `<cognee_memories>` recall injection returns expected memory content
