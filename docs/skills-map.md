# Карта skills и rules (autotests-ai-tms-automator)

Skills: `.cursor/skills/<name>/SKILL.md`  
Rules: `.cursor/rules/*.mdc`

**Принцип:** skill = workflow; rule = лимиты. Канон `automate-manual-test` — **только в этом репо**.

## Rules

| Rule | Scope | Назначение |
|------|-------|------------|
| `project-map` | always | Templates, RAG, TestOps flow |
| `agent-scope` | always | Один чат = одна зона |
| `session-cleanup` | always | Остановка серверов агента |
| `java-e2e-tests` | `templates/tests-java/**`, `projects/**` | Java e2e naming + CI |
| `rag-retrieval` | bootstrap, `projects/**`, generator | Vendored `docs/rag/` |
| `e2e-debug-run` | `templates/tests-java/**` | Отладочный прогон |
| `compose-from-primitives` | always | Не выдумывать UI |
| `layout-standard` | `templates/vanilla-ui/**` | Breakpoints, tokens |
| `component-sizes` | `templates/vanilla-ui/**` | Размеры примитивов |
| `component-edit` | `templates/vanilla-ui/**` | Микроправки CSS |
| `frontend-preview` | `templates/vanilla-ui/**` | file:// preview |

## Skills — e2e / TestOps

| Skill | Когда |
|-------|--------|
| `automate-manual-test` | TestOps → Java e2e в project repo |
| `give-manual-testcase` | «дай ручную» → TestOps кейс + ссылки |
| `bootstrap-project-repo` | Новый GitHub repo, sync template |

## Skills — vanilla UI

| Skill | Когда |
|-------|--------|
| `add-component` | Новый UI-примитив |
| `component-edit` | Микроправка одного элемента |
| `header-layout` | Сборка header |
| `header-config` | `window.headerConfig` |
| `embed-header` | Header в login/consumer page |
| `playground-verify` | Проверка harness pages |

## Skills — meta

| Skill | Когда |
|-------|--------|
| `sync-agent-meta` | После паттерна — rules/skills/RAG |
| `sync-rag` | Vendored `docs/rag/` из zero-design-system |

## RAG

| | Путь |
|---|------|
| Runtime (agent + automator) | `docs/rag/` — vendored, коммитится |
| Maintainer (SSOT) | `zero-design-system/docs/rag/` |
| Sync | `python scripts/sync_rag_from_template_project.py` |
| Skill | `sync-rag` |
| Rule | `.cursor/rules/rag-retrieval.mdc` |

## Как вызывать

| Фраза | Skill |
|-------|-------|
| «автоматизируй кейс TestOps» | `automate-manual-test` |
| «дай ручную» / «дай ручной кейс» | `give-manual-testcase` |
| «bootstrap test repo» | `bootstrap-project-repo` |
| «встрой header» | `embed-header` |
| «синхронизируй мету» | `sync-agent-meta` |
| «обнови rag» / «sync rag» | `sync-rag` |

## Templates

| Путь | Роль |
|------|------|
| `templates/tests-java/` | SSOT e2e эталон + GitHub bootstrap (trim в automator) |
| `templates/vanilla-ui/` | Static UI для local/генерации |
