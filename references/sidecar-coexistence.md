# Cognee sidecar coexistence with LanceDB Pro

## Verified target shape

Use this shape when you want LanceDB Pro to own `plugins.slots.memory` while Cognee still performs its own recall/sync lifecycle work.

- `plugins.slots.memory = memory-lancedb-pro`
- `plugins.entries.memory-lancedb-pro.enabled = true`
- original `plugins.entries.cognee-openclaw.enabled = false`
- cloned sidecar plugin `plugins.entries.cognee-sidecar-openclaw.enabled = true`
- sidecar plugin manifest must **not** declare `kind: "memory"`

## Why this is required

OpenClaw enforces the memory slot for plugins that declare `kind: "memory"`.

Live result that was reproduced on 2026-03-21:

- `memory-lancedb-pro` with `enabled: true` but **without** owning `plugins.slots.memory` is auto-disabled by runtime
- runtime message: `plugin disabled (memory slot set to "cognee-openclaw")`

So a memory plugin cannot coexist by being merely enabled. If Cognee keeps `kind: "memory"`, it must compete for the same slot and loses coexistence.

## Sidecar conversion rule

Do **not** try to make Cognee a different slot-based plugin kind.

Use the safer shape:

1. clone the plugin to a new id, e.g. `cognee-sidecar-openclaw`
2. remove `kind` from `openclaw.plugin.json`
3. patch runtime metadata in `dist/src/plugin.js`
   - change plugin `id`
   - remove `kind: "memory"`
4. patch any setup logic that force-writes `plugins.slots.memory = "cognee-openclaw"`
5. keep the lifecycle hooks intact:
   - `before_agent_start`
   - `agent_end`
   - any prompt/model hooks used for recall injection

## What was live-verified

With this shape active on Scott#1:

### LanceDB Pro side
- runtime registered `memory-lancedb-pro@1.0.32`
- `openclaw status` reported memory plugin = `memory-lancedb-pro`
- `openclaw memory-pro import` succeeded
- `openclaw memory-pro search` returned the imported test memory
- `openclaw memory-pro delete <uuid>` succeeded for a UUID-shaped test record
- follow-up list confirmed the deleted UUID record was gone

### Cognee sidecar side
- startup auto-sync still ran
- recall still ran
- log still showed memory injection happening
- gateway stayed healthy during the coexistence test

## Important caveat about deletes

`openclaw memory-pro delete` validates ID format more strictly than `memory-pro import`.

Observed behavior:
- import accepted a non-UUID test id
- delete rejected that non-UUID id as invalid
- delete succeeded for a UUID-shaped id

So for deterministic delete-path validation, always use UUID-form ids in test imports.

## Minimal config pattern

```json
{
  "plugins": {
    "slots": {
      "memory": "memory-lancedb-pro"
    },
    "allow": [
      "memory-lancedb-pro",
      "cognee-sidecar-openclaw"
    ],
    "entries": {
      "memory-lancedb-pro": {
        "enabled": true,
        "config": {
          "embedding": {
            "provider": "openai-compatible",
            "apiKey": "${SILICONFLOW_API_KEY}",
            "model": "BAAI/bge-m3",
            "baseURL": "https://api.siliconflow.cn/v1",
            "dimensions": 1024
          },
          "dbPath": "~/.openclaw/memory/lancedb-pro",
          "autoCapture": true,
          "autoRecall": false,
          "enableManagementTools": true,
          "retrieval": {
            "mode": "hybrid",
            "rerank": "none"
          },
          "sessionMemory": {
            "enabled": false,
            "messageCount": 15
          }
        }
      },
      "cognee-openclaw": {
        "enabled": false
      },
      "cognee-sidecar-openclaw": {
        "enabled": true,
        "config": "same-config-shape-as-original-cognee-openclaw"
      }
    }
  }
}
```

## Success criteria

Do not call coexistence complete until all are true:

1. gateway stays healthy
2. `memory-lancedb-pro` owns the memory slot
3. Cognee sidecar still logs auto-sync / recall activity
4. LanceDB Pro can import + search + delete in the coexistence state
5. Cognee sidecar still injects recall results
