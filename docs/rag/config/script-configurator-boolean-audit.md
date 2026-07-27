---
id: script-configurator-boolean-audit
domain: config
phase: 9.platform
tags: [script, configurator-boolean, design-system, greedy-token]
---
# script-configurator-boolean-audit

**id:** `script-configurator-boolean-audit`

Deterministic drift gate for the `configurator-boolean` canon — JSON stdout for `pipeline: meta-audit configurator-boolean`. Reads the design-system SSOT (seg template, remote-hub grid, seg/grid CSS, control-height token, presets/catalog) and asserts the deprecated toggle/flagstrip selectors stay removed.

## Файлы

- `scripts/configurator-boolean-audit.py` — self-contained (stdlib only)
- Skill: `.cursor/skills/configurator-boolean/SKILL.md`

## Входы

`--root PATH` (monorepo root), `--base REL` (default `projects/design-system-home/design-system`), optional `--dry-run`

## Assert

Exit 0 + `"ok": true` when: `plaque-field-seg` template exposes true|false; `plaque-field-grid-remote-hub` is `--mixed` with 3× `__cell--md` and enableVnc/enableVideo/enableHar (no headless); seg/grid CSS + `--plaque-control-height` present; `#remote-hub` preset + `#section-plaque-field` catalog exist; no `plaque-field--toggle` / `__indicator` / `-toggles` / `-flagstrip` / `--bool4` in canon css/templates.

## Do

- Run as step of `pipeline: meta-audit configurator-boolean` instead of re-reading the canon in agent chat
- Pair with `sync-agent-meta` when a new configurator-boolean pattern/запрет lands

## Don't

- Flag the `fv-*` exploration sandboxes (boolean-plaque-variants.html) — tokens are anchored on the `plaque-field` prefix
- Re-derive the invariants in chat — run the script
