---
id: docker-canon
domain: config
phase: 4a
tags: [config, docker, compose, dockerfile, dev, prod]
---

# Docker canon

SSOT: `docs/docker/DOCKER-CANON.md` · prod reboot: `docs/docker/prod-reboot.md`.

Эталон Docker/Compose для stack templates, workspace dev, generators и prod VM.

## Файлы

| Путь | Роль |
|------|------|
| `docs/docker/DOCKER-CANON.md` | Hub — версии, блоки, команды |
| `docs/docker/prod-reboot.md` | Prod VM reboot policy |
| `projects/autotests-ai-multistack-home/autotests-ai-multistack-app/docker-compose.yml` | Default-cell compose (postgres + java-spring + ts-react) |
| `projects/autotests-ai-multistack-home/autotests-ai-multistack-app/docker-compose.prod.yml` | Prod override (`restart: unless-stopped`) |
| `projects/autotests-ai-multistack-home/autotests-ai-multistack-app/backend/java/backend-java-spring/Dockerfile` | Multi-stage temurin 21 |
| `projects/autotests-ai-multistack-home/dev/docker-compose.yml` | Dev nginx proxy |
| `projects/selenoid-home/dev/` | Selenoid hub (native binary, не compose) |

## Входы / Assert

- Engine **29.6.1**, Compose **5.3.1**, API **1.55** (legacy Selenoid prod: Engine 26.1, API 1.45)
- Compose Spec — **без** `version:`
- CLI: `docker compose` (не `docker-compose`)
- Postgres internal only + `pg_isready` healthcheck
- Backend `depends_on: condition: service_healthy`
- Prod: `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build`

## Do

- Именовать bridge network `<app>_internal`, volume `pgdata`
- `.dockerignore` в `backend/` (`build/`, `.gradle/`, `src/test/`)
- Secrets через `.env` (gitignored); template vars через `render.sh`
- `includeDocker: false` в preset → render без compose/Dockerfile
- Selenoid: `DOCKER_API_VERSION=1.55`, SSOT `dev/browsers.json`
- Prod compose в git upstream — не править только на сервере

## Don't

- Публиковать postgres наружу
- `restart: no` на prod VM
- `depends_on` без healthcheck для postgres
- Копировать весь repo в Docker build context
- Hub Selenoid в docker-compose (native binary + browser images)
- Смешивать Docker API 1.45 с Engine 29.x
