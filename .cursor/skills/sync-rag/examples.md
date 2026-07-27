# Examples: sync-rag

## После правки чанка в zero-design-system

```bash
# zero-design-system — правка docs/rag/testing/test-taxonomy.md
cd autotests-ai-tms-automator
python scripts/sync_rag_from_template_project.py --check   # покажет changed: …
python scripts/sync_rag_from_template_project.py
git status docs/rag docs/adr
```

## CI / pre-commit check

```bash
python scripts/sync_rag_from_template_project.py --check || exit 1
```

## zero-design-system на другом пути

```bash
TEMPLATE_PROJECT_DIR=/Users/me/work/zero-design-system \
  python scripts/sync_rag_from_template_project.py
```

## Новый чанк hdr-layout-gap

1. zero-design-system: `docs/rag/testing-header/hdr-layout-gap.md` + строка в `manifest.jsonl`
2. automator: `python scripts/sync_rag_from_template_project.py`
3. bootstrap project repos подхватят RAG из vendored `docs/rag/` при следующем `ensure_repository()`
