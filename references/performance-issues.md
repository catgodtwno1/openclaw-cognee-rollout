## Known performance issues (2026-03-25)

### TCP connection leak in litellm embedding

**Symptom:** Cognee search latency degrades over time. `netstat` shows hundreds of ESTABLISHED connections to SiliconFlow.

**Root cause:** `litellm.aembedding()` creates new `httpx.AsyncClient` connections per call without pooling. When `asyncio.wait_for` timeout cancels requests, connections leak. Default `litellm.request_timeout = 6000` (100 minutes!) keeps leaked connections alive.

**Fix:** In Cognee container, edit `/app/.venv/lib/python3.12/site-packages/cognee/infrastructure/databases/vector/embeddings/LiteLLMEmbeddingEngine.py`:

```python
# After litellm.set_verbose = False
litellm.request_timeout = 30.0  # Prevent 6000s default causing connection leak
```

**Verification:**
```bash
docker exec cognee python3 -c "
with open('/proc/net/tcp') as f:
    lines = f.readlines()[1:]
    est = sum(1 for l in lines if int(l.split()[3],16)==1)
    print(f'TCP ESTABLISHED: {est}')
"
# Should be <10, not hundreds
```

### GRAPH_COMPLETION search mode causes 30s timeouts

**Symptom:** Cognee search requests timeout at 30s. Logs show vector retrieval + graph projection complete in <1s, but HTTP response never returns.

**Root cause:** Default `search_type = GRAPH_COMPLETION` calls LLM for answer generation after retrieval. If LLM is slow (MiniMax, etc.), the request hangs until gunicorn timeout.

**Fix:** Always use `search_type = "CHUNKS"` (pure vector search, no LLM post-processing). OpenClaw plugin config:

```json
{
  "searchType": "CHUNKS"
}
```

**Impact on stress tests:** The 11% failure rate in 500-round stress tests was caused by this — the test script used default GRAPH_COMPLETION mode, not the CHUNKS mode OpenClaw actually uses. Production is unaffected.

### Single worker limitation

Cognee runs `gunicorn -w 1` (single worker). One stuck request blocks all others. Cannot increase workers because SQLite + LanceDB don't support concurrent writes. This is a design constraint, not a bug.

