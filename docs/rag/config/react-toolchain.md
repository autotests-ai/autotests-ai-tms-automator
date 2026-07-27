---
id: react-toolchain
domain: config
phase: 9.react-pilot
tags: [react, typescript, vite, vitest, pnpm, toolchain]
related: [007-react-component-library]
---
# React frontend toolchain (memo)

**id:** `react-toolchain`  
**ADR:** [007-react-component-library](../../adr/007-react-component-library.md)

Рекомендации для pilot `packages/react-ui/`. Без обязательного внедрения TS7 RC в CI до стабилизации ecosystem.

## Package manager

| | pnpm (recommended) | npm |
|--|-------------------|-----|
| Disk | content-addressable store, hard links | дубли per project |
| Monorepo | `pnpm-workspace.yaml`, strict deps | workspaces OK, слабее isolation |
| CI cache | `pnpm store path` + lockfile | `npm ci` + `~/.npm` |

**Pilot:** npm в root `package.json` workspaces (минимальный diff). **Следующий шаг:** pnpm при >1 frontend package.

## Bundler

| Use case | Tool |
|----------|------|
| Library build | **tsup** — ESM + `.d.ts`, fast, малый config |
| Demo / dev | **Vite** — HMR для `demo/` |
| App production | Vite build |

**Не делать сейчас:** Webpack, CRA, Next.js для design-system library.

## Test

- **Vitest** — тот же config ecosystem что Vite; быстрый watch.
- **@testing-library/react** + **@testing-library/user-event** — component layer.
- **jsdom** — default environment для React Testing Library.
- **@testing-library/jest-dom** — matchers в `setup.ts`.

Target pilot: full suite < 30s local, CI step < 2 min.

## TypeScript

| Version | Когда |
|---------|-------|
| **TS 6.x** (stable) | Pilot, CI default, programmatic API (eslint plugins, vite plugins) |
| **TS 7 RC** (Go/native) | Локальный benchmark на `packages/react-ui/`; не блокер pilot |

TS7 даёт ~3–10× faster typecheck на больших проектах. Programmatic API стабилен с **7.1** — до этого держать TS6 для tooling chain.

### Upgrade path

1. Pilot on TS 6.x + `tsc --noEmit` in CI.
2. Optional local: `npm i -D typescript@rc`, compare `time tsc` vs TS6.
3. Переключить CI typecheck на TS7 когда eslint/vite plugins подтверждены.
4. Fallback: pin `typescript@6` в `package.json` при регрессии.

### Не делать сейчас

- Миграция всего monorepo на TS7 RC.
- Замена `tsc` на experimental wrappers в CI без benchmark log.
- Добавление `@typescript/native-preview` в production consumer apps.

## Monorepo layout

```
package.json          # workspaces: ["packages/*"]
packages/
  react-ui/
    package.json      # @zero-design-system/react
    src/
    demo/             # Vite pilot screen
    tsup.config.ts
    vitest.config.ts
```

Primitive CSS: vendored copy or path alias to `examples/java-spring/preview/css/` на pilot; long-term — sync script from `design-system/`.

## CI cache policy

- Cache key: lockfile hash + node version.
- Cache paths: `~/.npm` or pnpm store, **не** `node_modules` целиком в artifact upload.
- `npm ci` / `pnpm install --frozen-lockfile` в CI.
- Fail build if `dist/` or `coverage/` accidentally staged.

## Disk policy

- Один lockfile в root.
- `npm run clean:frontend` — удаляет `packages/*/node_modules`, `dist`, `.vite`, `coverage`, `*.tsbuildinfo`.
- Не ставить Storybook до явного ADR amendment.
- `generated-projects/` и `video/` — уже gitignored; не дублировать в frontend packages.

## Do

- Pin exact versions в pilot `package.json`.
- `sideEffects: false` в library package для tree-shaking.
- Separate `devDependencies` для demo-only tooling.

## Don't

- Commit `node_modules/`, `dist/`, `.vite/`.
- Add second package manager without ADR update.
- Use React 19 + strict TS + Storybook + Playwright component CT в одном pilot PR.
