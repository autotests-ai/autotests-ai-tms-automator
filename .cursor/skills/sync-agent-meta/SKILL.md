---
name: sync-agent-meta
description: >-
  Синхронизировать skills, rules и docs после завершённой доработки или смены
  фазы. Use when user asks to update skills/rules, sync meta, close a phase,
  or after a feature introduced a new pattern or constraint.
---

# Sync agent meta

Обновить **только** артефакты агента и канона. Код UI — в отдельном чате, если ещё не смержен.

**SSOT фаз и skills:** `docs/skills-map.md` — единый machine-readable канон. Зеркала (README, CONTEXT, project-map, skills-map, prompt-map) обновлять **после** manifest.

## 0. Триггер — есть ли что фиксировать?

Продолжать, если выполнено ≥1:

- новый паттерн сборки / naming / порядок чатов
- новое ограничение или запрет
- смена фазы или статуса skill (`planned` → `active`)
- новый примитив, влияющий на downstream skills
- явное расхождение между кодом и docs

**Стоп**, если правка — разовая микроправка без паттерна. Сообщить: «мета не нужна» и кратко почему.

### Смена фазы — порядок

1. **`docs/skills-map.md`** — `activePhase`, `completed`, `backlog`, `deferred`, `skills.*`, `rag.domains`
2. Зеркала: `README.md`, `docs/CONTEXT.md`, `.cursor/rules/project-map.mdc` (одинаковая формулировка `activePhase`)
3. `docs/skills-map.md`, `.cursor/skills/README.md`, `templates/vanilla-ui/js/prompt-map.js` — при смене skill-статуса
4. `./scripts/check-meta-sync.sh` — должен пройти без ERROR

## 1. Классификация (куда писать)

| Тип знания | Куда | Пример |
|------------|------|--------|
| **Фазы, skill-статусы (SSOT)** | `docs/skills-map.md` | `activePhase`, `skills.active` |
| Жёсткий лимит, запрет | `.cursor/rules/*.mdc` | «≤15 строк CSS», «не копировать монолитный header» |
| Пошаговый workflow | `.cursor/skills/<name>/SKILL.md` | чеклист `add-component` |
| Индекс и статусы | `docs/skills-map.md` | active / planned, таблица фраз |
| Снимок фазы | `docs/CONTEXT.md` + `project-map.mdc` | зеркало manifest |
| Необратимое решение | `docs/adr/NNN-*.md` | greenfield vs copy-paste header |
| E2e-паттерн для retrieval | `docs/rag/<domain>/<id>.md` + `manifest.jsonl` | `cfg-base-url`, `hdr-layout-gap` |
| Размеры UI | `docs/component-sizes.md` | новый токен / слот |

**Не дублировать:** rule = лимит; skill = как делать; ADR = почему; **rag chunk = как (retrieval)**; `skills-map` = оглавление; **manifest = SSOT фаз**.

## 2. Чеклист синхронизации

1. Прочитать diff / итог чата — выписать 1–3 **решения** (не список файлов).
2. Для каждого решения — строка в таблице §1 → целевой файл.
3. При смене фазы/skill → сначала `docs/skills-map.md`, потом зеркала.
4. Обновить `docs/skills-map.md`:
   - статус skill, фразы вызова, секция текущей фазы
4.5. Новый skill/rule → `templates/vanilla-ui/js/prompt-map.js` (UI `prompt-builder.html`)
5. Если сменилась фаза → `docs/CONTEXT.md` + `.cursor/rules/project-map.mdc` (одинаковая формулировка с manifest).
6. Если затронут skill-workflow → правка **только** релевантного `SKILL.md` (шаг «После изменений», пути, запреты).
7. Если новый примитив → `component-sizes.md` уже в `add-component`; проверить ссылки в `header-layout` / rules.
8. **Не** создавать новый skill/rule без явного паттерна (≥2 будущих использований).
9. Diff меты: ≤3 файла, без рефакторинга соседних секций.

## 3. Формат записи решения

В `skills-map.md` / `CONTEXT.md` — таблица:

| Тема | Канон |
|------|-------|
| … | одно предложение, путь к файлу |

В skill — в конец checklist: «После изменений → …».

## 4. Верификация

```bash
./scripts/check-meta-sync.sh
```

Скрипт проверяет:

- [ ] `activePhase` из manifest встречается в README, CONTEXT, project-map (строка «следующ»)
- [ ] каждый `skills.active` → `.cursor/skills/<id>/SKILL.md`
- [ ] `prompt-map.js` skills ⊆ manifest (active + planned + consumer)
- [ ] нет skill-папок вне manifest
- [ ] `docs/rag/manifest.jsonl` — файлы существуют, `id` совпадает с frontmatter

Ручной чеклист:

- [ ] Нет противоречий между `project-map.mdc` и `CONTEXT.md`
- [ ] `skills-map.md`, `.cursor/skills/README.md` и `templates/vanilla-ui/js/prompt-map.js` согласованы
- [ ] Нет копипасты одного правила в rule и skill
- [ ] Deprecated явно помечен в `docs/skills-map.md`

## Запреты

- Массовый рерайт всех skills «для красоты»
- Перенос антипаттернов consumer-репо в rules без ADR
- Обновление меты в том же чате, где ломается layout (сначала откат/фикс UI)
- Смена фазы только в зеркалах без обновления `docs/skills-map.md`
