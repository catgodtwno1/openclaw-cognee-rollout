## NAS Deployment Notes (QNAP/Synology)

### Docker network requirement

Same as MemOS: default bridge network does NOT support container DNS. Create a custom network:

```bash
$DOCKER network create oc-memory
$DOCKER network connect oc-memory oc-cognee-api
$DOCKER network connect oc-memory oc-qdrant
$DOCKER network connect oc-memory oc-neo4j
```

### Cognee user account on NAS

NAS Cognee uses the same default user: `default_user@example.com` / `default_password`. All data belongs to this user. Do NOT switch to a different user unless you want a fresh empty dataset.

### NAS-specific image build notes

- UV timeout: set `UV_HTTP_TIMEOUT=300` in Dockerfile `ENV` (NAS download speed may be slow)
- Pre-pull base image: `docker pull python:3.12-slim` before build
- Embedding dimension: set `EMBEDDING_DIMENSION=1024` for bge-m3 compatibility

### Persisting Cognee patches on NAS

Same strategy as MemOS:
1. Bind mount patched files (e.g., LiteLLMEmbeddingEngine.py)
2. Docker commit as backup image

```bash
$DOCKER cp oc-cognee-api:/app/.venv/lib/python3.12/site-packages/cognee/infrastructure/databases/vector/embeddings/LiteLLMEmbeddingEngine.py /path/to/LiteLLMEmbeddingEngine_patched.py

# Bind mount on recreate:
-v /path/to/LiteLLMEmbeddingEngine_patched.py:/app/.venv/lib/python3.12/site-packages/cognee/infrastructure/databases/vector/embeddings/LiteLLMEmbeddingEngine.py
```

