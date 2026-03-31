# NAS Deployment (updated 2026-03-31)

## Current NAS Stack (10.10.10.66)

| Container | Image | Ports | Status |
|-----------|-------|-------|--------|
| oc-neo4j | neo4j:2026.02.3 | 7474, 7687 | 3,671 Memory nodes (legacy MemOS) |
| oc-postgres | pgvector/pgvector:pg16 | 5432 | Hindsight DB, 1,712+ memories |
| oc-cognee | cognee-fixed:v5 | 8000 | M2.7-HS, 3 datasets |
| oc-hindsight | ghcr.io/vectorize-io/hindsight:latest | 9077, 9999 | M2.7-HS |

**Removed:** MemOS, Qdrant (replaced by LanceDB-Pro + Cognee + Hindsight)

## SSH Access

```bash
ssh openclaw@10.10.10.66  # Passwordless ed25519 key
```

## Docker on QNAP

Docker compose path varies by QNAP model:
```bash
# Try these in order:
docker compose ...
/share/CACHEDEV1_DATA/.qpkg/container-station/bin/docker-compose ...
```

⚠️ QNAP Container Station may have different docker-compose paths. Check with `which docker-compose` or `find / -name docker-compose 2>/dev/null`.

## NAS Cognee Configuration

Same as local but with NAS-specific paths:

```yaml
# docker-compose.yml (relevant section)
oc-cognee:
  image: cognee-fixed:v5
  ports:
    - "0.0.0.0:8000:8000"
  environment:
    LLM_MODEL: openai/MiniMax-M2.7-highspeed
    LLM_ENDPOINT: https://api.minimaxi.com/v1
    LLM_ARGS: '{"max_tokens":8192,"timeout":120}'
    LLM_MAX_COMPLETION_TOKENS: "8192"
    EMBEDDING_MODEL: openai/BAAI/bge-m3
    EMBEDDING_ENDPOINT: https://api.siliconflow.cn/v1
    EMBEDDING_DIMENSIONS: "1024"
    # ... (same env as local)
```

## Data Migration History

- 3,486 memories imported from NAS Qdrant → local Cognee (dataset: nas-import)
- 1,290 memories synced local Hindsight → NAS Hindsight
- NAS serves as backup/archive, local (老大) is primary

## NAS Role

- **Cold backup:** Holds complete imported data from legacy MemOS/Qdrant
- **Neo4j archive:** 3,671 Memory nodes from MemOS era (read-only reference)
- **Not primary:** All 4 Mac minis point to 老大 (10.10.20.178) for live Cognee, not NAS
