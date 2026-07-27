---
id: script-openapi-diff
domain: stacks
phase: 9.platform
tags: [script, openapi, contract, greedy-token]
---
# script-openapi-diff

**id:** `script-openapi-diff`

Diff `stacks/_contract/openapi.yaml` paths/operations — gate `contract_lint` for java-matrix-fanout and contract-fanout.

## Файлы

- `scripts/openapi-diff.py`
- `stacks/_contract/openapi.yaml` — SSOT contract

## Входы

`--root`, `--baseline`, optional `--candidate`, `--dry-run`

## Assert

Breaking = removed paths or changed HTTP methods on shared paths.

## Do

- Run before fan-out when contract changes
- Phase A: file-vs-file only (no live export)

## Don't

- Use LLM to compare OpenAPI — use this script
