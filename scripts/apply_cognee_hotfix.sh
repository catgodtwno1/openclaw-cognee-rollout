#!/usr/bin/env bash
set -euo pipefail

CONTAINER="${COGNEE_CONTAINER:-cognee}"
HEALTH_URL="${COGNEE_HEALTH_URL:-http://127.0.0.1:8000/health}"

if command -v colima >/dev/null 2>&1 && colima status >/dev/null 2>&1; then
  export DOCKER_HOST="${DOCKER_HOST:-unix:///Users/scott/.colima/default/docker.sock}"
fi

python_patch='from pathlib import Path
files=[
"/app/cognee/infrastructure/databases/vector/embeddings/LiteLLMEmbeddingEngine.py",
"/app/.venv/lib/python3.12/site-packages/cognee/infrastructure/databases/vector/embeddings/LiteLLMEmbeddingEngine.py",
"/app/.venv/lib64/python3.12/site-packages/cognee/infrastructure/databases/vector/embeddings/LiteLLMEmbeddingEngine.py",
]
old="# Pass through target embedding dimensions when supported\n                    if self.dimensions is not None:\n                        embedding_kwargs[\"dimensions\"] = self.dimensions"
new="# OpenClaw hotfix: dimensions suppressed for compatibility"
for f in files:
    p=Path(f)
    if not p.exists():
        continue
    s=p.read_text()
    if old in s:
        p.write_text(s.replace(old,new))
        print("patched dimensions suppression:", f)
'

python_dims='from pathlib import Path
files=[
"/app/cognee/infrastructure/databases/vector/embeddings/config.py",
"/app/.venv/lib/python3.12/site-packages/cognee/infrastructure/databases/vector/embeddings/config.py",
"/app/.venv/lib64/python3.12/site-packages/cognee/infrastructure/databases/vector/embeddings/config.py",
]
for f in files:
    p=Path(f)
    if not p.exists():
        continue
    s=p.read_text()
    ns=s.replace("embedding_dimensions: Optional[int] = 3072","embedding_dimensions: Optional[int] = 1024")
    if ns != s:
        p.write_text(ns)
        print("patched embedding_dimensions=1024:", f)
'

docker exec "$CONTAINER" python - <<PY
${python_patch}
${python_dims}
PY

docker restart "$CONTAINER" >/dev/null

for _ in $(seq 1 30); do
  if curl -fsS "$HEALTH_URL" >/dev/null 2>&1; then
    curl -fsS "$HEALTH_URL"
    exit 0
  fi
  sleep 2
done

echo "Cognee did not become healthy in time" >&2
exit 1
