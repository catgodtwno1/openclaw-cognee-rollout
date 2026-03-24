#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path

DEFAULT_CONFIG = Path("/Users/scott/.openclaw/openclaw.json")
DEFAULT_CLONE_SCRIPT = Path("/Users/scott/.openclaw/workspace/skills/openclaw-cognee-rollout/scripts/make_cognee_sidecar_clone.py")
DEFAULT_BACKUP = Path("/Users/scott/.openclaw/backups/openclaw-sidecar-toggle")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def save_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def ensure_list_unique(items: list[str], value: str) -> None:
    if value not in items:
        items.append(value)


def ensure_path(cfg: dict, path: list[str], default):
    cur = cfg
    for key in path[:-1]:
        cur = cur.setdefault(key, {})
    return cur.setdefault(path[-1], default)


def backup_config(config_path: Path, backup_dir: Path) -> Path:
    backup_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    dst = backup_dir / f"openclaw.json.{ts}.bak"
    shutil.copy2(config_path, dst)
    return dst


def clone_exists() -> bool:
    return Path("/Users/scott/.openclaw/extensions/cognee-sidecar-openclaw/openclaw.plugin.json").exists()


def apply_mode(config_path: Path, backup_dir: Path) -> dict:
    data = load_json(config_path)
    backup = backup_config(config_path, backup_dir)

    plugins = data.setdefault("plugins", {})
    allow = plugins.setdefault("allow", [])
    entries = plugins.setdefault("entries", {})
    slots = plugins.setdefault("slots", {})

    ensure_list_unique(allow, "memory-lancedb-pro")
    ensure_list_unique(allow, "cognee-openclaw")
    ensure_list_unique(allow, "cognee-sidecar-openclaw")

    if "cognee-openclaw" not in entries:
        raise SystemExit("plugins.entries.cognee-openclaw is missing; cannot derive sidecar config")

    cognee_entry = entries["cognee-openclaw"]
    sidecar_entry = entries.setdefault("cognee-sidecar-openclaw", {})
    if "config" not in sidecar_entry and "config" in cognee_entry:
        sidecar_entry["config"] = json.loads(json.dumps(cognee_entry["config"]))
    sidecar_entry["enabled"] = True

    cognee_entry["enabled"] = False

    lancedb_entry = entries.setdefault("memory-lancedb-pro", {})
    lancedb_entry["enabled"] = True

    slots["memory"] = "memory-lancedb-pro"

    save_json(config_path, data)
    return {
        "backup": str(backup),
        "slot_memory": slots.get("memory"),
        "cognee_enabled": entries["cognee-openclaw"].get("enabled"),
        "sidecar_enabled": entries["cognee-sidecar-openclaw"].get("enabled"),
        "lancedb_enabled": entries["memory-lancedb-pro"].get("enabled"),
    }


def revert_mode(config_path: Path, backup_dir: Path) -> dict:
    data = load_json(config_path)
    backup = backup_config(config_path, backup_dir)

    plugins = data.setdefault("plugins", {})
    entries = plugins.setdefault("entries", {})
    slots = plugins.setdefault("slots", {})

    if "cognee-openclaw" not in entries:
        raise SystemExit("plugins.entries.cognee-openclaw is missing; cannot revert")

    entries["cognee-openclaw"]["enabled"] = True
    if "cognee-sidecar-openclaw" in entries:
        entries["cognee-sidecar-openclaw"]["enabled"] = False
    if "memory-lancedb-pro" in entries:
        entries["memory-lancedb-pro"]["enabled"] = False

    slots["memory"] = "cognee-openclaw"

    save_json(config_path, data)
    return {
        "backup": str(backup),
        "slot_memory": slots.get("memory"),
        "cognee_enabled": entries["cognee-openclaw"].get("enabled"),
        "sidecar_enabled": entries.get("cognee-sidecar-openclaw", {}).get("enabled"),
        "lancedb_enabled": entries.get("memory-lancedb-pro", {}).get("enabled"),
    }


def status_mode(config_path: Path) -> dict:
    data = load_json(config_path)
    plugins = data.get("plugins", {})
    entries = plugins.get("entries", {})
    slots = plugins.get("slots", {})
    return {
        "slot_memory": slots.get("memory"),
        "cognee_enabled": entries.get("cognee-openclaw", {}).get("enabled"),
        "sidecar_enabled": entries.get("cognee-sidecar-openclaw", {}).get("enabled"),
        "lancedb_enabled": entries.get("memory-lancedb-pro", {}).get("enabled"),
        "sidecar_clone_exists": clone_exists(),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Toggle between original Cognee memory mode and LanceDB Pro + Cognee sidecar mode")
    ap.add_argument("command", choices=["apply", "revert", "status"])
    ap.add_argument("--config", default=str(DEFAULT_CONFIG), help="Path to openclaw.json")
    ap.add_argument("--backup-dir", default=str(DEFAULT_BACKUP), help="Backup directory for openclaw.json snapshots")
    args = ap.parse_args()

    config_path = Path(args.config)
    backup_dir = Path(args.backup_dir)

    if not config_path.exists():
        raise SystemExit(f"Config not found: {config_path}")

    if args.command == "apply":
        if not clone_exists():
            raise SystemExit(
                "Sidecar clone is missing. Run: python3 skills/openclaw-cognee-rollout/scripts/make_cognee_sidecar_clone.py --force"
            )
        result = apply_mode(config_path, backup_dir)
    elif args.command == "revert":
        result = revert_mode(config_path, backup_dir)
    else:
        result = status_mode(config_path)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
