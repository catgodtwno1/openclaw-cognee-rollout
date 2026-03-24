#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


def patch_text(text: str) -> str:
    text = text.replace('id: "cognee-openclaw",', 'id: "cognee-sidecar-openclaw",')
    text = text.replace('name: "Memory (Cognee)",', 'name: "Cognee Sidecar",')
    text = text.replace(
        'description: "Cognee-backed memory with multi-scope support (company/user/agent), session tracking, and auto-recall",',
        'description: "Cognee sidecar with multi-scope support (company/user/agent), session tracking, and auto-recall",',
    )
    text = text.replace('    kind: "memory",\n', '')
    text = text.replace('config.plugins.slots.memory = "cognee-openclaw";\n', '')
    text = text.replace(
        'entries["cognee-openclaw"] ??= { enabled: true };\n                entries["cognee-openclaw"].enabled = true;\n',
        'entries["cognee-sidecar-openclaw"] ??= { enabled: true };\n                entries["cognee-sidecar-openclaw"].enabled = true;\n',
    )
    text = text.replace(
        'console.log("  - Memory slot set to cognee-openclaw");\n',
        'console.log("  - Running as non-slot sidecar plugin");\n',
    )
    text = text.replace('console.log("Cognee memory setup complete (hybrid mode):");', 'console.log("Cognee sidecar setup complete (hybrid mode):");')
    text = text.replace('console.log("Cognee memory setup complete:");', 'console.log("Cognee sidecar setup complete:");')
    return text


def main() -> int:
    ap = argparse.ArgumentParser(description="Clone cognee-openclaw into a non-memory sidecar plugin")
    ap.add_argument("--source", default="/Users/scott/.openclaw/extensions/cognee-openclaw", help="Source Cognee plugin directory")
    ap.add_argument("--dest", default="/Users/scott/.openclaw/extensions/cognee-sidecar-openclaw", help="Destination sidecar plugin directory")
    ap.add_argument("--force", action="store_true", help="Overwrite destination if it exists")
    args = ap.parse_args()

    src = Path(args.source)
    dst = Path(args.dest)

    if not src.exists():
        raise SystemExit(f"Source plugin not found: {src}")
    if dst.exists():
        if not args.force:
            raise SystemExit(f"Destination already exists: {dst} (use --force)")
        shutil.rmtree(dst)

    shutil.copytree(src, dst)

    manifest_path = dst / "openclaw.plugin.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["id"] = "cognee-sidecar-openclaw"
    manifest["name"] = "Cognee Sidecar"
    manifest.pop("kind", None)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")

    package_path = dst / "package.json"
    package = json.loads(package_path.read_text())
    package["name"] = "@cognee/cognee-sidecar-openclaw"
    package["description"] = "OpenClaw Cognee sidecar plugin with auto-recall/capture (non-memory-slot)"
    package_path.write_text(json.dumps(package, ensure_ascii=False, indent=2) + "\n")

    runtime_path = dst / "dist" / "src" / "plugin.js"
    runtime_path.write_text(patch_text(runtime_path.read_text()))

    print(f"Created sidecar clone: {dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
