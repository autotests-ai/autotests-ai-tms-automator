---
name: sync-rag
description: >-
  Sync vendored docs/rag from zero-design-system (SSOT) into autotests-ai-tms-automator.
  Use when user asks to update RAG, sync rag, refresh rag chunks, or after
  editing docs/rag in zero-design-system.
---

# Sync RAG (zero-design-system → automator)

Base: `projects/autotests-ai-home/autotests-ai-tms-automator/`

## Модель

| Роль | Путь | Кто правит |
|------|------|------------|
| **SSOT maintainer** | `zero-design-system/docs/rag/` | zero-design-system |
| **Vendored runtime** | `autotests-ai-tms-automator/docs/rag/` | только через sync |
| **ADR (002, 003)** | копируются в `docs/adr/` | sync вместе с RAG |

Automator, bootstrap и agent **читают** vendored `docs/rag/` — не абсолютный путь к zero-design-system.

Env: `TEMPLATE_PROJECT_DIR` — источник для sync-скрипта (default: `/Users/stanislav/zero-design-system`).

## Когда вызывать

- Пользователь: «обнови rag», «sync rag», «скопируй чанки из zero-design-system»
- После правки/добавления чанка в **zero-design-system** `docs/rag/`
- Перед bootstrap/generate, если `--check` падает

**Стоп**, если правят только `docs/rag/` **в automator** вручную — перенести правку в zero-design-system, потом sync.

## Workflow for agent

### 1. Проверить источник

```bash
test -d "${TEMPLATE_PROJECT_DIR:-/Users/stanislav/zero-design-system}/docs/rag" \
  && echo "RAG source OK" || echo "STOP: zero-design-system недоступен"
```

### 2. Проверить drift (без записи)

```bash
cd projects/autotests-ai-home/autotests-ai-tms-automator
python scripts/sync_rag_from_template_project.py --check
```

### 3. Sync

```bash
python scripts/sync_rag_from_template_project.py
python scripts/sync_rag_from_template_project.py --check   # должен exit 0
```

Override пути:

```bash
python scripts/sync_rag_from_template_project.py \
  --template-project-dir /path/to/zero-design-system
```

### 4. Что попадает в automator

| Источник | Назначение |
|----------|------------|
| `docs/rag/testing/` | e2e чанки |
| `docs/rag/testing-header/` | header чанки |
| `docs/rag/manifest.jsonl` | индекс |
| `docs/rag/README.md` | оглавление |
| `docs/adr/002-e2e-canonical-patterns.md` | ADR |
| `docs/adr/003-header-smoke-e2e.md` | ADR |

### 5. Новый чанк (в zero-design-system)

1. Создать `docs/rag/<domain>/<id>.md` с frontmatter (`id`, `domain`, `phase`, `tags`)
2. Строка в `docs/rag/manifest.jsonl`
3. Одна строка в ADR 002 или 003 (id → path) — skill `sync-agent-meta`, если меняется scope
4. **Sync в automator** — этот skill
5. Commit vendored `docs/rag/` (+ `docs/adr/` если изменились) в automator

## Rules

- `.cursor/rules/rag-retrieval.mdc` — runtime читает vendored копию
- Не править `docs/rag/` в automator без sync из SSOT
- Не править zero-design-system из automator-чата (кроме явного запроса в том workspace)

## DoD

- [ ] `python scripts/sync_rag_from_template_project.py --check` → exit 0
- [ ] `manifest.jsonl` и файлы чанков на месте в `docs/rag/`
- [ ] ADR 002/003 синхронизированы, если менялись в zero-design-system
- [ ] Пользователь знает: commit в automator — vendored копия; SSOT — zero-design-system

См. `examples.md`.
