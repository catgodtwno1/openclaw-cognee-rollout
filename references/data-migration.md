## Data Migration (跨機器遷移)

### When to migrate

- Moving from local Docker (Colima) to NAS
- Consolidating multiple machines' Cognee data
- Disaster recovery

### What can be migrated

| Data | Method | Notes |
|------|--------|-------|
| LanceDB vectors | rsync (files) | Full fidelity, cross-platform |
| SQLite metadata | rsync (file) | Included in databases/ dir |
| Graph data (kuzu) | ❌ Not compatible with neo4j | Requires re-cognify on destination |
| Graph data (neo4j → neo4j) | Neo4j dump/load | Same DB engine only |
| User accounts | ❌ Manual | Must pre-exist on destination |

### Migration script

```bash
# Local Mac → NAS via SSH
bash scripts/cognee_migrate.sh \
  --src-path ~/.local/share/cognee/databases \
  --dst-host openclaw@<NAS_HOST> \
  --dst-path /share/CACHEDEV1_DATA/Container/openclaw-memory/cognee-data/databases \
  --stop-container \
  --dst-docker /share/CACHEDEV1_DATA/.qpkg/container-station/bin/docker

# Dry run first
bash scripts/cognee_migrate.sh \
  --src-path ~/.local/share/cognee/databases \
  --dst-host openclaw@<NAS_HOST> \
  --dst-path /share/path/databases \
  --dry-run

# Local-to-local (Docker volume → backup)
bash scripts/cognee_migrate.sh \
  --src-path /var/lib/docker/volumes/cognee/_data/databases \
  --dst-path /backup/cognee-databases
```

### Finding source data path

| Environment | Typical path |
|-------------|-------------|
| macOS Colima | `~/.local/share/cognee/databases` or Docker volume |
| Docker bind mount | Whatever `-v` points to |
| NAS QNAP | `/share/CACHEDEV1_DATA/Container/openclaw-memory/cognee-data/databases` |

To find the actual path inside a running container:
```bash
docker exec oc-cognee-api python3 -c "import cognee; print(cognee.config.data_root_directory)"
```

### Known pitfalls

1. **Graph DB incompatibility**: macOS Cognee typically uses **kuzu**; NAS Cognee uses **neo4j**. Graph relationships can't transfer between them. LanceDB vectors still work — Cognee can search by vector without graph, but `GRAPH_COMPLETION` search mode won't work until re-cognified.

2. **NAS /tmp is tiny**: QNAP `/tmp` is a 64MB tmpfs. Never use `tar` to `/tmp`. Use rsync direct transfer.

3. **rsync "failed to set times" warning**: Harmless on NAS — QNAP doesn't support setting mtime on some mount points. Data is still transferred correctly.

4. **User isolation**: All data belongs to a specific Cognee user (typically `default_user@example.com`). The destination Cognee must use the **same user account** or the data won't be visible.

5. **Stop container during transfer**: LanceDB files can corrupt if Cognee writes during rsync. Stop the destination container first (`--stop-container` flag).

### Post-migration verification

```bash
# Restart destination Cognee
docker restart oc-cognee-api

# Run smoke test
python3 scripts/cognee_smoke_test.py --base-url http://DEST_IP:8766

# Run stress test (search only — don't add until verified)
python3 scripts/cognee_stress_test.py --url http://DEST_IP:8766 --mode search --rounds 50

# If graph DB changed (kuzu → neo4j), optionally re-cognify:
# Login → POST /api/v1/cognify with a small test dataset
```

### Complete migration checklist

- [ ] Stop destination Cognee container
- [ ] Run rsync of `databases/` directory
- [ ] Verify file count matches source
- [ ] Start destination Cognee container
- [ ] Confirm `/` returns "I am alive"
- [ ] Login with correct user (`default_user@example.com`)
- [ ] Search returns results from migrated data
- [ ] Run stress test (50+ rounds, zero errors)
- [ ] Update OpenClaw configs on all client machines to point to new server

