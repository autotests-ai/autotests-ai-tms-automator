---
id: script-java-matrix-plan
domain: testing
phase: 9.platform
tags: [script, java-matrix, qa-guru-refs, greedy-token]
---
# script-java-matrix-plan

**id:** `script-java-matrix-plan`

Build fan-out manifest from qa-guru-refs `schema/stack-matrix.yaml` for platform-sync-agent.

## Файлы

- `scripts/java-matrix-plan.py`
- External: `../qa-guru-home/qa-guru-refs/schema/stack-matrix.yaml`

## Входы

`--refs-root`, `--source gradle-junit5-selenide`, optional `--targets`, `--dry-run`

Env: `QA_GURU_REFS_ROOT`

## Assert

JSON with `run_id`, `targets[]` each pointing to `autotests-java-agent` params.

## Do

- Source anchor ≈ ethalon `generators/ethalon/tests-java/` (`java-gradle-junit5-selenide`)
- Default: all 17 other Java combos as targets

## Don't

- Hardcode 18 combos in agent chat — read matrix SSOT
