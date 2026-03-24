#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_PATH="${HOME}/.openclaw/openclaw.json"
SEARCH_TYPE="CHUNKS"
BASE_URL=""
DATASET_NAME=""
SKIP_INDEX=0
SKIP_SMOKE=0

usage() {
  cat <<'EOF'
Usage:
  onboard_cognee_client.sh --base-url http://SERVER_IP:8000 [--dataset-name NAME] [--config PATH] [--search-type CHUNKS]

What it does:
  1. Patch local cognee-openclaw plugin
  2. Configure OpenClaw to use the shared Cognee service
  3. Reset local Cognee sync state
  4. Run index
  5. Run smoke test

Options:
  --base-url URL        Required. Cognee service base URL
  --dataset-name NAME   Optional. Defaults to openclaw-<normalized-hostname>
  --config PATH         Optional. Defaults to ~/.openclaw/openclaw.json
  --search-type TYPE    Optional. Defaults to CHUNKS
  --skip-index          Configure/reset only; skip `openclaw cognee index`
  --skip-smoke          Skip smoke test
  -h, --help            Show help
EOF
}

normalize_hostname() {
  local raw
  raw="$(scutil --get ComputerName 2>/dev/null || hostname)"
  raw="${raw,,}"
  raw="${raw// /-}"
  raw="$(printf '%s' "$raw" | tr -cd 'a-z0-9-')"
  raw="${raw#-}"
  raw="${raw%-}"
  printf '%s' "${raw:-client}"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --base-url) BASE_URL="$2"; shift 2 ;;
    --dataset-name) DATASET_NAME="$2"; shift 2 ;;
    --config) CONFIG_PATH="$2"; shift 2 ;;
    --search-type) SEARCH_TYPE="$2"; shift 2 ;;
    --skip-index) SKIP_INDEX=1; shift ;;
    --skip-smoke) SKIP_SMOKE=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown arg: $1" >&2; usage; exit 1 ;;
  esac
done

if [[ -z "$BASE_URL" ]]; then
  echo "--base-url is required" >&2
  usage
  exit 1
fi

if [[ -z "$DATASET_NAME" ]]; then
  DATASET_NAME="openclaw-$(normalize_hostname)"
fi

echo "==> Patch local plugin"
python3 "$SCRIPT_DIR/patch_openclaw_cognee_plugin.py"

echo "==> Configure OpenClaw client"
python3 "$SCRIPT_DIR/configure_openclaw_cognee_client.py" \
  --config "$CONFIG_PATH" \
  --base-url "$BASE_URL" \
  --dataset-name "$DATASET_NAME" \
  --search-type "$SEARCH_TYPE"

echo "==> Reset local Cognee sync state"
mkdir -p "${HOME}/.openclaw/memory/cognee"
printf '{}' > "${HOME}/.openclaw/memory/cognee/datasets.json"
printf '{"entries":{}}' > "${HOME}/.openclaw/memory/cognee/sync-index.json"

if [[ "$SKIP_INDEX" -eq 0 ]]; then
  echo "==> Run index"
  openclaw cognee index
fi

if [[ "$SKIP_SMOKE" -eq 0 ]]; then
  echo "==> Run smoke test"
  python3 "$SCRIPT_DIR/cognee_smoke_test.py" --base-url "$BASE_URL" --dataset-name "$DATASET_NAME"
fi

echo "Done. datasetName=$DATASET_NAME baseUrl=$BASE_URL"
