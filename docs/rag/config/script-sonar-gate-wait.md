---
id: script-sonar-gate-wait
domain: config
phase: 9.platform
tags: [script, sonar, quality-gate, greedy-token]
---
# script-sonar-gate-wait

**id:** `script-sonar-gate-wait`

Poll **sonar.qa.guru** quality gate API until PASSED/FAILED — gate `sonar_quality_gate`.

## Файлы

- `scripts/sonar-gate-wait.py`

## Входы

`--url https://sonar.qa.guru`, `--project-key`, `--timeout`, `--poll`, `--dry-run`

Env: `SONAR_TOKEN` (never in argv)

## Assert

Exit 0 when status is OK/PASSED; JSON includes `dashboard_url`.

## Do

- Use `--dry-run` for local smoke without token
- Wire into platform-sync-agent before `status=ready`

## Don't

- Pass token on command line
