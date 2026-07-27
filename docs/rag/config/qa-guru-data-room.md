# QA Guru data room — historical summary (RAG-safe)

Compact index for agents. **No** raw HTML, homework PII, credentials, or DB passwords.

## Canonical paths (local)

| Layer | Path |
|-------|------|
| Live lesson inventory (L1) | `projects/qa-guru-home/exports/lesson-content-export/live-20260712-143557/` |
| Metrics/homework bundle (L2) | `projects/qa-guru-home/exports/migration-export/bundle/2026-07-12/` |
| Users raw (L0) | `projects/qa-guru-home/exports/commercial-export/raw/` (gitignored) |
| Deals raw (L5) | `projects/qa-guru-home/exports/commercial-export/raw/` (gitignored) |
| Surveys raw (L4) | `projects/qa-guru-home/exports/survey-export/raw/` (gitignored) |
| Webinars raw (L14) | `projects/qa-guru-home/exports/webinar-export/raw/` (gitignored) |
| Mailings raw (L11) | `projects/qa-guru-home/exports/mailing-export/raw/` (gitignored) |
| Payments raw (L5b) | `projects/qa-guru-home/exports/commercial-export/raw/` (gitignored) |
| Bitrix raw | `projects/qa-guru-home/integrations/bitrix-home/bitrix-export/raw/` (gitignored) |
| Albato recon / bundle | `projects/qa-guru-home/integrations/albato-home/` (gitignored raw/recon/inbox) |
| BotHelp raw | `projects/qa-guru-home/integrations/bothelp-home/raw/` (gitignored) |
| Metrika raw (L15) | `projects/qa-guru-home/exports/metrika-export/raw/` (gitignored) |
| UniSender raw (L16) | `projects/qa-guru-home/exports/unisender-export/raw/` (gitignored) |
| SendPulse raw | `projects/qa-guru-home/integrations/sendpulse-home/raw/` (gitignored; aggregate counts only in RAG) |
| Power BI semantic tables | `projects/qa-guru-home/integrations/powerbi-home/` (gitignored `*.csv`) |
| Import bundle copy | `/tmp/qa-guru-migration-export/2026-07-12/` |
| Data room reports | `docs/qa-guru/data-room/` |
| LMS import | `migration-export/scripts/import-training.py` |

## Quality gates (frozen 2026-07-12)

| Gate | Result | Notes |
|------|--------|-------|
| Live crawl vs local DB | **MATCH** | 135 trainings, 5009 unique lessons, `streams_skipped=0` |
| G3 metrics export | **PASS** | Counts match SQL; join keys OK; 8 orphan lessons documented |
| G4 LMS dry-run (Java 42) | **PASS** | 50 lessons, 380 homework rows, 0 missing lesson ids |
| LMS apply (Java 42) | **done** | See `docs/qa-guru/data-room/lms-apply-42.json` |
| Phase B content (Java 42) | **done** | 50/50 `lecture.content` via `import-lecture-content.py` |
| L0 users API export | **done** | 9738 rows, 69 fields — see `commercial-coverage.md` |
| L5 deals API export | **done** | 11576 rows, 86 fields — P&L/unit-economics |
| L4 surveys crawl | **done** | 2830 surveys, 12005 responses, gap=0 — see `survey-coverage.md` |
| L5b payments | **done** | 4659 rows — see `payments-coverage.md` |
| L14 webinars | **done** | 38 rooms, 55 broadcasts — see `webinar-coverage.md` |
| L11 mailings | **done** | 695 campaigns, 645 with stats — see `mailing-coverage.md` |
| L6/L8 groups | **done** | 326 groups, 16572 enrollments — see `groups-coverage.md` |
| L13 custom fields | **done** | `custom-fields.json` |
| Bitrix identity graph | **live** | 25508 edges; 70.2% user / 25.7% deal; metrics student→GC 99.4% — `identity-coverage.md` |
| Email join spec | **done** | GC/US/SP overlap — `email-join-spec.md` |
| Albato dedupe | **done** | 55 duplicate order groups — `albato-dedupe.md` |
| Attribution recon | **done** | Metrika ↔ GC ↔ Power BI — `metrika-attribution.md` |
| Albato join spec | **verified (API)** | Bundle 347148 field map via Headless API; email/phone → deal UF codes |
| BotHelp raw | **done** | 1570 subscribers; Telegram join **deferred** |
| L15 Metrika | **done** | Counter 64794919; export 2026-07-13 — `metrika-coverage.md` |
| L16 UniSender | **done** | 43 lists, 15113 contacts, 43 campaigns + L16b extended — `unisender-coverage.md` |
| SendPulse | **done** | 117 books, 620 campaigns; email→GC in identity graph — `sendpulse-coverage.md` |
| Power BI tables | **done** | Manual CSV SSOT — `powerbi-ssot.md`, `powerbi-tables-coverage.md` |
| eLama spend | **blocked** | `limited_billing` — `elama-spend-coverage.md` |

## Raw lake layers (summary)

| Layer | Rows (aggregate) | Notes |
|-------|------------------|-------|
| L0 users | 9738 | Export API; email/phone/UTM |
| L1 lessons | 5009 | Live crawl |
| L2 homework | 15583 answers | metrics bundle |
| L4 surveys | 12005 responses / 2830 surveys | UI crawl; paginated; gap=0 |
| L5 deals | 11576 | Export API; cost/paid/income |
| L5b payments | 4659 | Export API; transaction-level |
| L6/L8 groups | 326 groups / 16572 enrollments | UI grid + L0 join; `enrollments-ui.jsonl` canonical |
| L11 mailings | 695 campaigns | UI crawl; 645 with delivery stats |
| L13 custom fields | 69 fields | L0 export field list + `custom-fields.json` |
| L14 webinars | 38 rooms, 55 broadcasts | UI crawl |
| L15 Metrika | done | Reporting API; qa.guru counter 64794919 |
| L16 UniSender | 43 lists / 15113 contacts / 43 campaigns | L16b: 90 templates, 42 messages, 41 delivery CSV |
| Bitrix CRM | core done (14571/6231/296) | REST webhook; full export via `run-bitrix-export.sh` |
| Identity graph | 25508 edges | GC↔B24 + L2 metrics + ESP emails — `scripts/qa-guru/build-identity-graph.py` |
| BotHelp subscribers | 1570 | Telegram join **deferred** |
| UniSender emails | 9828 (5478→GC) | Tier 1 in `email-join-spec.md` |
| SendPulse emails | 13017 (7358→GC) | Tier 1 in `email-join-spec.md` |
| L3 lesson comments | — | Phase C deferred |
| Power BI semantic | 42618 fact + 2979 guide | Manual CSV SSOT; `powerbi-ssot.md` |

## Stream index (Wave1 Java)

| Stream | training_id | Live lessons | Metrics homework (bundle) |
|--------|-------------|--------------|---------------------------|
| 38 | 934706175 | 50 | — |
| 39 | 934964279 | 49 | — |
| 40 | 935071088 | 45 | 566 |
| 41 | 935222411 | 44 | 465 |
| 42 | 935536915 | **50** | 380 |
| 43 | 935573308 | **48** | — |

Legacy dirs `java-38..43` are **not** SSOT — use `live-*` snapshot.

## Known drifts / fixes

1. **Hidden lessons + submodule BFS** — `getcourse-import-data` parser; fixed Java 42 (45→50) and 43 (10→48).
2. **Metrics lesson count** — prod metrics 5145 vs live crawl 5009 (8 orphan `lesson.training_id` in metrics).
3. **Identity gap** — `metrics.users` has no email; LMS import uses synthetic `{ext_id}@{ext_id}.ru`.
4. **Status mapping** — RU GC strings → `StudentHomeWorkStatus` enum (see `GETCOURSE-MIGRATION.md`).

## LMS import mapping (summary)

- `training.ext_id` ← metrics `training.id`
- `lecture.ext_id` ← metrics `lesson.id`
- `student_home_work.ext_id` ← `answer.id` (`gc_answer_id`)
- Comments ← `answer_comment` aggregated in `homework.jsonl`

## Reproduce (local only)

```bash
# Live inventory + compare
cd projects/qa-guru-home/integrations/getcourse-home/getcourse-import-data
scripts/run-lesson-audit.sh --content=false --out=../lesson-content-export/live-<stamp>

# Metrics bundle (SSH tunnel qa-guru-sync)
cd projects/qa-guru-home/exports/migration-export
bash scripts/run-local-metrics-export.sh

# Data room reports
python projects/qa-guru-home/scripts/build-data-room-reports.py

# LMS dry-run / apply (stream 42)
python migration-export/scripts/import-training.py --training-id 935536915 \
  --export-dir /tmp/qa-guru-migration-export/2026-07-12
python migration-export/scripts/import-training.py --training-id 935536915 --apply

# Phase B lecture content (stream 42)
python migration-export/scripts/import-lecture-content.py --training-id 935536915 --apply

# L0 + L5 commercial raw (API key in .env.local)
cd projects/qa-guru-home/exports/commercial-export && ./run-commercial-export.sh

# L4 surveys (UI login GC_EMAIL/GC_PASSWORD)
cd projects/qa-guru-home/exports/survey-export
python export-surveys.py --full

# L5b payments
cd projects/qa-guru-home/exports/commercial-export
python export-payments.py

# L6 enrollments (UI canonical) + L8 index
python export-groups-ui.py --resume
python build-enrollments.py

# L14 webinars + L11 mailings
python projects/qa-guru-home/exports/webinar-export/export-webinars.py
python projects/qa-guru-home/exports/mailing-export/export-mailings.py --include-draft --resume

# Albato bundle capture (manual or Embedded API)
cd projects/qa-guru-home/integrations/albato-home
python import-bundle-spec.py
./run-albato-export.sh

# Bitrix full raw + identity graph (B24_WEBHOOK_URL in .env.local or ~/.config/bitrix/env)
cd projects/qa-guru-home/integrations/bitrix-home/bitrix-export
python recon-bitrix.py && ./run-bitrix-export.sh
WITH_ACTIVITIES=1 ./run-bitrix-export.sh   # optional
# Join reports (monorepo root)
python scripts/qa-guru/build-identity-graph.py
python scripts/qa-guru/build-email-join-spec.py
python scripts/qa-guru/build-albato-dedupe-report.py
python scripts/qa-guru/build-metrika-attribution-report.py

# L15 Metrika (YANDEX_METRIKA_TOKEN in ~/.config/yandex-metrika/env)
cd projects/qa-guru-home/exports/metrika-export
./run-metrika-export.sh

# L16 UniSender (UNISENDER_API_KEY in ~/.config/unisender/env)
cd projects/qa-guru-home/exports/unisender-export
python verify-unisender-key.py
./run-unisender-export.sh
./run-unisender-extended.sh --resume
```

## Do not put in RAG

- `lesson-content.jsonl` bodies / `raw_html`
- Full `homework.jsonl` / `answer.jsonl` text
- `commercial-export/raw/*.jsonl` (PII)
- `survey-export/raw/*.jsonl` (PII)
- `webinar-export/raw/` HTML (PII)
- `mailing-export/raw/` (PII)
- `bitrix-home/bitrix-export/raw/` (PII)
- `bitrix-home/bitrix-export/recon/` (field schemas may contain samples)
- `albato-home/raw/`, `albato-home/recon/`, `albato-home/inbox/bundle-spec.json`
- `metrika-export/raw/` (traffic aggregates)
- `unisender-export/raw/` (contacts PII, delivery-stats, visited-links, message/template HTML)
- `powerbi-home/*.csv` (deal/lead names, CRM ids)
- `.env`, `.env.local`, Telegram tokens, GC passwords, `GC_API_KEY`, `ALBATO_MASTER_TOKEN`, `ALBATO_EMAIL`/`ALBATO_PASSWORD`, `YANDEX_METRIKA_TOKEN`, `UNISENDER_API_KEY`

## References

- `docs/qa-guru/data-room/DATA-ROOM-INDEX.md`
- `docs/qa-guru/HALLUCINATION-AUDIT-GATES.md` (G3/G4)
- `projects/qa-guru-home/exports/migration-export/GETCOURSE-MIGRATION.md`
