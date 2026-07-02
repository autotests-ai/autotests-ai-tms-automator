# ADR 004: Fast TestOps launch (warm pool + 3-run)

## Status

Accepted (design). Warm pool wiring — PoC in `selenoid-home/warm-pool-orchestrator/`.

## Context

Baseline локально (2 smoke, no artifacts): `gradle test` ~6 с, clean ~3 с.

TestOps automation: `@AllureId` известен при генерации (`test_java.py`); для статуса **Active (-3)** нужен `allureReportMode=allure3` + `allurectl upload`, не `none`.

CI GitHub Actions: cold runner + checkout + Selenoid session + attachments → минуты wall-clock.

## Decision

### Env profiles

| Profile | Run | Назначение |
|---------|-----|------------|
| `fast-testops` | 1, 2 | Warm pool, lean browser, Allure minimal |
| `ci` | 3 | Diagnostic: video, screenshot, pageSource, debug logs |

### 3-run strategy

```
Run 1 (fast):  warm pool + preopen + -Denv=fast-testops
               @AllureId в коде → allurectl upload → TestOps green → STOP

Run 2 (fast):  те же ключи, если Run 1 red (новый reserve/preopen)
               green → flake, комментарий в TestOps; Run 3 не нужен
               red   → Run 3

Run 3 (diag):  -Denv=ci (+ VNC/cold Selenoid опционально)
               тот же @AllureId → upload с полным отчётом
```

### Invariants

1. `@AllureId("{testOpsId}")` — в generated test с первого коммита.
2. Run 1–2: **не** `allureReportMode=none` — только attach/listener off.
3. `@Tag("visual")` — отдельный job, вне fast path.
4. Co-located Jenkins: persistent workspace, `skipHealthCheck=true`, Gradle daemon.

### Success criteria

| Metric | Target |
|--------|--------|
| Run 1 green wall-clock | ≤ 5 с |
| TestOps после Run 1 | Active (-3), без video |
| Run 3 rate | ≪ 10% прогонов |

## Warm pool integration (MVP)

Orchestrator: `selenoid-home/warm-pool-orchestrator/` (`:9090`).

```
Jenkins trigger
  ├─ POST /pool/reserve
  ├─ POST /pool/preopen { baseUrl + login.html }   ← parallel с Gradle
  ├─ ./gradlew test -Denv=fast-testops -DremoteUrl=${WEBDRIVER_URL} …
  ├─ allurectl upload build/allure-results
  └─ POST /pool/release
```

Lean slot image: `webdriver-image` with `WARM_VIDEO=false`, `ENABLE_VNC=false`, `--headless=new`.

Planned Gradle flags (Java wiring follow-up):

| Flag | Meaning |
|------|---------|
| `-Dwarm_driver=true` | Attach to reserved slot |
| `-Dwarm_slot_id=` | From reserve response |
| `-Dpreopen_url=` | Skip `open()` if URL already loaded |

Example shell: `templates/tests-java/scripts/testops-fast-launch.example.sh`.

## Agent prompt (warm-pool MVP)

```markdown
## Goal

Implement fast TestOps UI test launch per ADR 004 in qa-guru-tms-automator + selenoid-home.

## Baseline

- 2 smoke: `LoginTests.shouldLoginWithValidCredentials`, `HeaderTests.externalLinksHaveHref`
- Local cold: gradle test ~6 s; pair duration ~3.8 s (Allure history)
- `@AllureId` on generated tests from TestOps id (already in test_java.py)

## Profiles

- Run 1/2: `-Denv=fast-testops` → `config/fast-testops.properties`
- Run 3: `-Denv=ci`
- 3-run shell: `templates/tests-java/scripts/testops-fast-launch.example.sh`

## Tasks

1. Timeline: cold GHA path vs warm co-located path (trigger → first assert).
2. Wire `TestBase` / custom WebDriverProvider for `-Dwarm_driver=true` + reserved session.
3. Optional `-Dpreopen_url`: skip Selenide `open()` when current URL matches.
4. Jenkins: integrate `selenoid-home/warm-pool-orchestrator/scripts/jenkins-preopen.example.sh`.
5. Lean image tweaks: `webdriver-image` entrypoint — no Xvfb when `WARM_VIDEO=false`.
6. Document risks: stale state (`/warm/reset` vs BrowserSessionHelper), preopen/Gradle race, slot affinity.

## Constraints

- One test case = one `@Test` with `@AllureId`
- Fast path: allure3 + zero attachments (not none)
- Visual tests excluded from fast job
- Minimal diff; no mass refactor

## Success

- 2 smoke ≤ 5 s wall on co-located Jenkins + warm pool
- TestOps Active (-3) after Run 1 upload without video
- Run 3 only after 2× fast red
```

## References

- `templates/tests-java/src/test/resources/config/fast-testops.properties`
- `selenoid-home/warm-pool-orchestrator/README.md`
- `.cursor/skills/automate-manual-test/SKILL.md` — `@AllureId`, TestOps finalize
