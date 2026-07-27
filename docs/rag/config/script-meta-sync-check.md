---
id: script-meta-sync-check
domain: config
phase: 9.platform
tags: [script, meta-sync, greedy-token]
---
# script-meta-sync-check

**id:** `script-meta-sync-check`

Native Python meta-sync validator — JSON stdout for platform-sync-agent gate `meta_sync_clean`. Checks phase-manifest SSOT, phase mirrors, skills, prompt-map, monorepo layout, RAG manifest.

## Файлы

- `scripts/meta-sync-check.py` — self-contained (no shell dependency)

## Входы

`--root PATH` (monorepo root), optional `--dry-run`

## Assert

Exit 0 + `"ok": true` when phase-manifest, skills, RAG manifest, layout checks pass.

## Do

- Call from `greedy-token pipeline "meta-audit …"` step 1
- Use `--dry-run` in CI bootstrap to validate paths before the full run

## Don't

- Reimplement manifest validation in agent chat — run the script
