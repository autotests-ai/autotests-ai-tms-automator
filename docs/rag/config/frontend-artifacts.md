---
id: frontend-artifacts
domain: config
phase: 9.react-pilot
tags: [react, node, artifacts, gitignore, cache, ci]
related: [react-toolchain, 007-react-component-library]
---
# Frontend artifacts — что коммитить и что чистить

**id:** `frontend-artifacts`  
**Script:** `npm run clean:frontend` → `scripts/clean-frontend.mjs`

## Gitignore (канон)

| Path | Причина |
|------|---------|
| `node_modules/` | deps |
| `dist/` | library + demo build |
| `.vite/` | Vite pre-bundle cache |
| `.turbo/` | turborepo cache (если появится) |
| `coverage/` | Vitest coverage |
| `storybook-static/` | Storybook build (если появится) |
| `*.tsbuildinfo` | TS incremental |
| `playwright-report/` | e2e reports |
| `test-results/` | Playwright artifacts |

## Коммитить

| Path | Причина |
|------|---------|
| `package.json` (root workspaces) | workspace config |
| `package-lock.json` | reproducible CI (`npm ci`) |
| `packages/react-ui/src/**` | source |
| `packages/react-ui/package.json` | package manifest |

## Не коммитить

- Любой `node_modules/` в root или packages
- `packages/react-ui/dist/` после `npm run build`
- Локальные `.env` с secrets

## Безопасная очистка

```bash
npm run clean:frontend
```

Удаляет cache/build dirs, **не** трогает `src/`, `demo/`, lockfile.

Ручная очистка при раздувании диска:

```bash
rm -rf node_modules packages/*/node_modules
npm ci
```

## CI cache policy

- Cache key: `package-lock.json` hash + Node version
- Cache: `~/.npm` (npm) — не upload `node_modules` как artifact
- Steps: `npm ci` → `npm run build:react-ui` → `npm run test:react-ui`
- Fail if `git status` shows `dist/` or `coverage/` after build

## generated-projects / video

Уже в root `.gitignore`:

- `generated-projects/*/`
- `video/` (untracked media)

Frontend packages **не** пишут в эти зоны.

## Do

- Run `clean:frontend` перед отчётом о disk usage
- Pin Node LTS in CI
- One lockfile at repo root

## Don't

- `git add node_modules` «для скорости»
- Commit Storybook static без explicit release
- Duplicate `package-lock.json` per package (npm workspaces = root lock only)
