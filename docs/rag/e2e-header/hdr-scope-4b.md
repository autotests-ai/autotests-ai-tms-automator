---
id: hdr-scope-4b
domain: e2e-header
phase: 4b
adr: 003
tags: [scope, header, frontend]
---
# Scope фазы 4b — header smoke

Target: `frontend/header.html` (harness). Gallery: `header-examples.html`. Отдельный чат/PR — не трогать login e2e и `header.css` без запроса.

| Параметр | Значение |
|----------|----------|
| App root | `http://localhost:3000/` (server cwd = `frontend/`) |
| Page | `/header.html` |
| Breakpoint | 768px (`layout-standard.md`) |
| Viewports | 390, 768, 769, 1280 |
| Epic | `Template Header` |

## 4b.1 (первый PR)

Behavioral smoke + layout probes. **Без PNG baselines.**

## 4.visual (opt-in)

Visual baselines: header harness + login + logged-in (`visual-baseline`). `-DincludeTags=visual`, `-DupdateBaselines=true`, отдельные `*BaselineTests`, отдельный PR.

## Don't

Landing, dashboard iframe, cross-page stability на one-page-form.
