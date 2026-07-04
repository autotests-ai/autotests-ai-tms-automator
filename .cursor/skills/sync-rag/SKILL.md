---
name: sync-rag
description: >-
  Sync vendored docs/rag from template-project (SSOT) into autotests-ai-tms-automator.
  Use when user asks to update RAG, sync rag, refresh rag chunks, or after
  editing docs/rag in template-project.
---

# Sync RAG (template-project → automator)

Base: `autotests-ai-tms-automator/`

## Модель

| Роль | Путь | Кто правит |
|------|------|------------|
| **SSOT maintainer** | `template-project/docs/rag/` | template-project |
| **Vendored runtime** | `autotests-ai-tms-automator/docs/rag/` | только через sync |
| **ADR (002, 003)** | копируются в `docs/adr/` | sync вместе с RAG |

Automator, bootstrap и agent **читают** vendored `docs/rag/` — не абсолютный путь к template-project.

Env: `TEMPLATE_PROJECT_DIR` — источник для sync-скрипта (default: `/Users/stanislav/template-project`).

## Когда вызывать

- Пользователь: «обнови rag», «sync rag», «скопируй чанки из template-project»
- После правки/добавления чанка в **template-project** `docs/rag/`
- Перед bootstrap/generate, если `--check` падает

**Стоп**, если правят только `docs/rag/` **в automator** вручную — перенести правку в template-project, потом sync.

## Workflow for agent

### 1. Проверить источник

```bash
test -d "${TEMPLATE_PROJECT_DIR:-/Users/stanislav/template-project}/docs/rag" \
  && echo "RAG source OK" || echo "STOP: template-project недоступен"
```

### 2. Проверить drift (без записи)

```bash
cd autotests-ai-tms-automator
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
  --template-project-dir /path/to/template-project
```

### 4. Что попадает в automator

| Источник | Назначение |
|----------|------------|
| `docs/rag/e2e/` | e2e чанки |
| `docs/rag/e2e-header/` | header чанки |
| `docs/rag/manifest.jsonl` | индекс |
| `docs/rag/README.md` | оглавление |
| `docs/adr/002-e2e-canonical-patterns.md` | ADR |
| `docs/adr/003-header-smoke-e2e.md` | ADR |

### 5. Новый чанк (в template-project)

1. Создать `docs/rag/<domain>/<id>.md` с frontmatter (`id`, `domain`, `phase`, `tags`)
2. Строка в `docs/rag/manifest.jsonl`
3. Одна строка в ADR 002 или 003 (id → path) — skill `sync-agent-meta`, если меняется scope
4. **Sync в automator** — этот skill
5. Commit vendored `docs/rag/` (+ `docs/adr/` если изменились) в automator

## Rules

- `.cursor/rules/rag-retrieval.mdc` — runtime читает vendored копию
- Не править `docs/rag/` в automator без sync из SSOT
- Не править template-project из automator-чата (кроме явного запроса в том workspace)

## DoD

- [ ] `python scripts/sync_rag_from_template_project.py --check` → exit 0
- [ ] `manifest.jsonl` и файлы чанков на месте в `docs/rag/`
- [ ] ADR 002/003 синхронизированы, если менялись в template-project
- [ ] Пользователь знает: commit в automator — vendored копия; SSOT — template-project

См. `examples.md`.
