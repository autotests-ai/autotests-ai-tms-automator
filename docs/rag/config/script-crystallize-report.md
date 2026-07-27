---
id: script-crystallize-report
domain: config
phase: 9.platform
tags: [script, crystallize, telemetry, greedy-token]
---
# script-crystallize-report

**id:** `script-crystallize-report`

Rank repeated cursor/ollama tasks from `~/.greedy-token/usage.jsonl` → crystallize candidates.

## Файлы

- `scripts/crystallize-report.py`
- Skill: `.cursor/skills/script-crystallize/SKILL.md`

## Входы

`--since 7d`, `--top 10`, optional `--usage PATH`

## Assert

JSON with `coverage_pct`, `candidates[]` with `suggested_script` ids.

## Do

- Run weekly; promote top patterns to `scripts/*.py` + RAG + routes
- Distinct from `greedy-token report` (billing footer)

## Don't

- Confuse with `greedy_token_usage` MCP tool
