---
name: ops-cognee-rollout
description: Deploy, repair, harden, and verify OpenClaw + Cognee memory on a Mac mini or shared Cognee server. Use when setting up Cognee from scratch, copying a known-good Cognee setup to another Mac mini, exposing one Mac mini as the Cognee service host for other OpenClaw clients, switching clients to a remote Cognee baseUrl, or troubleshooting Cognee failures involving Docker/Colima, SiliconFlow, embedding dimensions, dataset corruption, recall not injecting, or cognee-openclaw update failures.
---

# OpenClaw Cognee Rollout

Use this skill to reproduce the working Cognee setup. Last validated: 2026-03-31.

## What this skill standardizes

- Run Cognee in Docker on one Mac mini
- Use SiliconFlow for both LLM and embedding
- Patch Cognee 0.5.5-local so `bge-m3` works with 1024-dim vectors
- Patch `cognee-openclaw` so update becomes replace-on-failure
- Convert Cognee into a non-slot sidecar when it must coexist with `memory-lancedb-pro`
- Point local or remote OpenClaw clients at the Cognee server
- Verify real recall, not just health

## Canonical known-good shape

- Cognee backend: `0.5.6-local` (Docker image: `cognee-fixed:v5`)
- LLM model: `openai/MiniMax-M2.7-highspeed` (via MiniMax API `api.minimaxi.com`)
- LLM max_tokens: `8192` (M2.7-HS reasoning model needs headroom for thinking + output)
- Embedding model: `openai/BAAI/bge-m3` (via SiliconFlow)
- Embedding dimensions: `1024`
- Search type: `CHUNKS`
- Port binding: `0.0.0.0:8000` (NOT `127.0.0.1` — other machines need LAN access)
- Working dataset: `openclaw-main-v7`
- Auth: disabled (`REQUIRE_AUTHENTICATION=false`)

### Model selection notes

| Model | Status | Notes |
|-------|--------|-------|
| SiliconFlow Qwen2.5-32B | ❌ | TPM rate limit on free tier |
| MiniMax M2.1-HS | ❌ | Thinking tokens overflow, zero JSON output |
| MiniMax M2.5-HS | ✅ | Works but nondeterministic |
| **MiniMax M2.7-HS** | ✅ **Best** | 100% success at max_tokens=8192 |

## Server vs client mode

### Server mode

Use one Mac mini as the Cognee host.

1. Ensure Colima/Docker works
2. Run Cognee container bound to the LAN, not just localhost
3. Apply the Cognee hotfix script from `scripts/apply_cognee_hotfix.sh`
4. Verify `/health`
5. Open the chosen host/port to LAN or tailnet clients

Use `references/server-mode.md` for the exact environment and run command.

### Client mode

Use another Mac mini as an OpenClaw client that talks to the shared Cognee host.

1. Patch the local `cognee-openclaw` plugin with `scripts/patch_openclaw_cognee_plugin.py`
2. Point `openclaw.json` to the remote `baseUrl`
3. Use a unique dataset name per machine unless you intentionally want a shared dataset
4. Re-index and run recall verification

Use `references/client-mode.md` for the exact config shape.

## Required fixes (baked into cognee-fixed:v5)

These patches are pre-applied in the Docker image `cognee-fixed:v5`. You only need to rebuild if starting from `cognee/cognee:latest`.

### PATCH1: Message role order fix

MiniMax requires system message at position 0. Cognee sends `[user, system]` order.

Files patched in litellm_instructor:
- `azure_openai/adapter.py`
- `gemini/adapter.py`
- `openai/adapter.py`
- `generic_llm_api/adapter.py`

### PATCH2: Embedding dimensions removal

SiliconFlow BAAI/bge-m3 rejects `dimensions=3072` parameter (HTTP 422).
`LITELLM_DROP_PARAMS=true` is insufficient — manually removed dimensions kwarg in `LiteLLMEmbeddingEngine`.

### Legacy patches (still available but rarely needed)

```bash
# Only needed if building from scratch without cognee-fixed:v5
bash skills/ops-cognee-rollout/scripts/apply_cognee_hotfix.sh
python3 skills/ops-cognee-rollout/scripts/patch_openclaw_cognee_plugin.py
```

## Configure a client quickly

Preferred generic method:

```bash
bash skills/openclaw-cognee-rollout/scripts/onboard_cognee_client.sh \
  --base-url http://SERVER_IP:8000
```

This does not depend on any specific machine name. It auto-generates a dataset name from the local hostname.

Manual method:

```bash
python3 skills/openclaw-cognee-rollout/scripts/configure_openclaw_cognee_client.py \
  --base-url http://SERVER_IP:8000 \
  --dataset-name openclaw-client-name \
  --search-type CHUNKS
```

Then run:

```bash
openclaw cognee index
```

## Cognee API Quick Reference

| 功能 | 方法 | 路径 | Content-Type | 说明 |
|------|------|------|-------------|------|
| Health | GET | `/health` | — | 返回 `{"status":"ready","health":"healthy"}` |
| Health (详细) | GET | `/health/detailed` | — | 含组件级状态 |
| Login | POST | `/api/v1/users/signin` | `application/json` | Body: `{"username":"...","password":"..."}` → 返回 `access_token` |
| Login (旧) | POST | `/api/v1/auth/login` | `application/x-www-form-urlencoded` | 仅 Cognee 0.5.5 旧版兼容 |
| Search | POST | `/api/v1/search` | `application/json` | Body: `{"query":"...","datasets":["openclaw-init"]}` ⚠️ 需 Bearer token |
| Add | POST | `/api/v1/add` | `multipart/form-data` | 上传文件/文本到 dataset |
| Cognify | POST | `/api/v1/cognify` | `application/json` | 触发知识图谱构建 |
| Datasets | GET | `/api/v1/datasets` | — | 列出所有 datasets |
| Settings | GET | `/api/v1/settings` | — | 查看当前配置 |

**⚠️ 常见错误路径（全部返回 404）：**
- ❌ `/search` → 正确：`/api/v1/search`
- ❌ `/api/v1/health` → 正确：`/health`
- ❌ `/api/v1/signin` → 正确：`/api/v1/users/signin`

## Verification rule

Do **not** stop at health or index counts.

Always verify all four:

1. `health` works
2. `index` works with `0 errors`
3. add / update / delete work
4. recall actually injects `<cognee_memories>` or `/api/v1/search` returns real memory hits

## Sidecar coexistence mode

Use this mode when `memory-lancedb-pro` must own `plugins.slots.memory` but Cognee still needs to keep its own sync/recall lifecycle.

Rules:

1. `memory-lancedb-pro` must own `plugins.slots.memory`
2. original `cognee-openclaw` must be disabled
3. cloned sidecar plugin (for example `cognee-sidecar-openclaw`) must be enabled
4. sidecar manifest must not declare `kind: "memory"`
5. sidecar setup logic must not write `plugins.slots.memory = "cognee-openclaw"`

Use this helper when you need to generate the sidecar clone deterministically:

```bash
python3 skills/openclaw-cognee-rollout/scripts/make_cognee_sidecar_clone.py --force
```

Use this helper when you need to switch the host between original Cognee memory mode and LanceDB Pro + Cognee sidecar mode:

```bash
python3 skills/openclaw-cognee-rollout/scripts/toggle_cognee_sidecar_mode.py status
python3 skills/openclaw-cognee-rollout/scripts/toggle_cognee_sidecar_mode.py apply
python3 skills/openclaw-cognee-rollout/scripts/toggle_cognee_sidecar_mode.py revert
```

`apply` writes a timestamped backup of `openclaw.json`, sets `plugins.slots.memory = "memory-lancedb-pro"`, enables `memory-lancedb-pro`, disables `cognee-openclaw`, and enables `cognee-sidecar-openclaw`.

`revert` writes a timestamped backup and returns to the original single-slot Cognee shape.

Do not try to keep two `kind: "memory"` plugins enabled and hope only one owns the slot. Runtime auto-disables the non-slot one.

Use:

```bash
python3 skills/openclaw-cognee-rollout/scripts/cognee_smoke_test.py --base-url http://HOST:8000
```

## When to create a fresh dataset

Create a fresh dataset if either is true:

- dataset status stays `DATASET_PROCESSING_ERRORED`
- historical bad updates polluted file pointers or vector schema state

Do not waste time trying to salvage a poisoned dataset unless the user explicitly asks.

## Read these references when needed

- `references/troubleshooting.md` — exact failures and fixes
- `references/server-mode.md` — how to expose one Mac mini as Cognee host
- `references/client-mode.md` — how another Mac mini connects to the shared host
- `references/validated-config.md` — the validated config and command shapes
- `references/sidecar-coexistence.md` — verified `memory-lancedb-pro` + Cognee sidecar coexistence pattern

## Known Cognee user accounts

| User | Password | ID | Notes |
|------|----------|----|-------|
| `default_user@example.com` | `default_password` | auto-created | Default owner. All data lives here when auth is disabled. |

**Current setup:** Auth is disabled (`REQUIRE_AUTHENTICATION=false`). All requests use default_user implicitly. No login needed.

**When auth is enabled:** The auth endpoint is `POST /api/v1/auth/login` with `Content-Type: application/x-www-form-urlencoded`.

## Multi-Machine Deployment (多台 Mac Mini 共用)

### User Account 策略

Cognee 有嚴格的多租戶隔離。**切換用戶 = 數據消失**。

| 場景 | 建議 | 原因 |
|------|------|------|
| 同一個人的多台機器 | **統一用 `default_user@example.com`** | 所有數據都在這個用戶名下（884 個 lance 文件） |
| 不同人共用 NAS Cognee | 各建各的用戶（但很少見） | 多租戶隔離 |

### OpenClaw 配置（每台機器的 openclaw.json）

```json
{
  "plugins": {
    "entries": {
      "cognee": {
        "config": {
          "baseUrl": "http://<COGNEE_HOST>:8000",
          "username": "default_user@example.com",
          "password": "default_password"
        }
      }
    }
  }
}
```

**⚠️ 關鍵規則：**
- 四台 Mac Mini **必須用同一個賬號**（`default_user@example.com / default_password`）
- **絕對不要**改成 `admin2@cognee.ai` 或其他賬號——會立刻看不到所有數據
- 之前踩過的坑：曾用 `admin2@cognee.ai`（ID: 95cf83e5），結果搜索全空，因為數據屬於 `default_user`（ID: f5249267）
- 新機器 onboard 時，直接用 `onboard_cognee_client.sh` 腳本，賬號已內建

### 與 MemOS 的差異

| | MemOS | Cognee |
|---|---|---|
| 隔離粒度 | `user_id` 字段（靈活） | 登錄賬號（嚴格） |
| 切換影響 | 只是搜索過濾不同 | **數據完全不可見** |
| 建議 | 共用 `scott` | 共用 `default_user@example.com` |
| 測試隔離 | 用不同 `user_id` | 用不同 `dataset`（不要換賬號） |

## Common pitfall: user identity mismatch

Cognee has multi-tenant isolation. If you change the username/password in config, the new user cannot see data owned by the old user. See `references/troubleshooting.md` #8 for full diagnosis and fix.

## Monitoring

Use the five-layer memory benchmark (from `ops-five-layer-memory` skill) for periodic health checks. It tests all 5 memory layers with timing data and can run as a cron job.

## Known performance issues

See [references/performance-issues.md](references/performance-issues.md) for TCP leak analysis, GRAPH_COMPLETION timeout, and single-worker bottleneck details.

## NAS Deployment Notes

See [references/nas-deployment.md](references/nas-deployment.md) for QNAP/Synology-specific configuration, Docker paths, and resource allocation.

## Cognee 壓測腳本

```bash
# 搜索壓測（預設 100 輪，NAS）
python3 scripts/cognee_stress_test.py --mode search

# 寫入壓測
python3 scripts/cognee_stress_test.py --mode add --rounds 50

# 搜索+寫入混合
python3 scripts/cognee_stress_test.py --mode both --rounds 50

# 指定 URL + 清理
python3 scripts/cognee_stress_test.py --url http://<COGNEE_HOST>:8000 --rounds 100 --cleanup
```

判定標準：
- ✅ PASS: search P95 < 5s + 零錯誤 + 衰退 ≤ 2.0x
- ⚠️ WARN: search P95 < 5s 但衰退 > 2.0x（連接泄漏/telemetry 可能未修）
- ❌ FAIL: search P95 ≥ 5s 或有錯誤

## Data Migration

See [references/data-migration.md](references/data-migration.md) for cross-machine migration (local→NAS, LanceDB vectors, graph DB compatibility, migration script, and post-migration checklist).

## Operational advice

- Prefer `CHUNKS` before fancier graph-style search while stabilizing rollout
- Prefer one dataset per client machine during rollout; merge later only if needed
- If Colima is running but Docker CLI is broken, fix `DOCKER_HOST` first
- After config changes, re-index from a clean sync index when necessary
- Keep secrets out of notes and skill files
- Periodically restart Cognee container (every 24h) as safety net against FD leaks
- Monitor TCP connections after heavy usage: `docker exec cognee` + `/proc/net/tcp`
