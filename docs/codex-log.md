# Codex build log

| Date | Milestone | Task | Outcome | Fix cycles | Commit |
|------|-----------|------|---------|-----------|--------|
| 2026-07-26 | 1 | Contract intake and full-project plan | Complete | 0 | ff69528 |
| 2026-07-26 | 1 | Day 1 implementation and verification | Complete | 4 | edf9d23 |
| 2026-07-26 | 2 | Intake pipeline plan | Complete | 0 | 1281749 |
| 2026-07-26 | 2 | CSV, router, and vision intake | Complete | 6 | 8c2fae3 |
| 2026-07-26 | 2.5 | Integration audit and sample-data plan | Complete | 0 | 9cea175 |
| 2026-07-26 | 2.5 | Audit and sample data | Complete | 5 | 7a9e3d8 |

## Historical context

`c5957d5` and `65c0a8c` predate this working agreement. They are an initial frontend prototype and are not backfilled with invented timestamps or test results.

---
### [2026-07-26 00:56 IST] Milestone 1 · contract intake and implementation plan

**Goal:** Establish the governing architecture and full roadmap before code.

**Plan:** Read `Agents.md`, `Spec.md`, `spec_patch_supabase.md`, and `design.md` in order; the patch overrides SQLite and password-login assumptions.

**Files touched:** `PLAN.md` (modified: eight-milestone roadmap and detailed Day 1 files), `docs/codex-log.md` (modified: logging table and entry).

**Generated:** Complete roadmap and detailed Day 1 sequence.

**Tests written first:** None; planning only. The plan requires HTTP and WebSocket tests before handlers.

**Run results:**
- Run 1: PASSED — all four governing documents read completely.

**Self-review:** Preserve the prototype only as pre-contract work; replace password login with Supabase Google/magic-link scaffolding while demo stays public.

**Time:** ~12 minutes. **Commit:** `ff69528` plan full project milestones.
---

### [2026-07-26 01:00 IST] Milestone 1 · API and WebSocket contract tests

**Goal:** Define health, public-demo, and agent-log contracts before FastAPI handlers.

**Plan:** Add Python configuration and black-box tests in `MOCK_MODE=true`; accept expected initial import failure.

**Files touched:** `backend/pyproject.toml`, `backend/tests/test_authz_api.py`, `backend/tests/test_ws_smoke.py`, `backend/tests/conftest.py` (created), `docs/codex-log.md` (modified).

**Generated:** Tests for health, anonymous demo access, and a five-field WebSocket event.

**Tests written first:** `test_health_reports_ready`, `test_anonymous_demo_store_is_available`, `test_agent_log_websocket_streams_a_structured_event`.

**Run results:**
- Run 1: FAILED — `MOCK_MODE=true python3 -m pytest backend/tests` — no pytest installed.
  → Cause: workspace Python lacked development dependencies.
  → Fix: created ignored `backend/.venv` and installed dependencies.
- Run 2: FAILED — `.venv/bin/pip install -e '.[dev]'` — Python 3.14.6 rejected `<3.12`; `python3.11` is unavailable.
  → Cause: local runner is newer than target.
  → Fix: package marker became `>=3.11`; CI remains Python 3.11.
- Run 3: FAILED — `MOCK_MODE=true .venv/bin/pytest tests` — `main` did not exist.
  → Cause: expected test-first application absence.
  → Fix: implemented the application in the next work unit.
- Run 4: PASSED — `MOCK_MODE=true .venv/bin/pytest tests` — 3 passed, 0 failed.

**Self-review:** Tests are contract-focused and need no Supabase credentials.

**Time:** ~10 minutes. **Commit:** `edf9d23` build milestone 1 foundation.
---

### [2026-07-26 01:06 IST] Milestone 1 · FastAPI service and Supabase foundation

**Goal:** Implement Day 1 APIs plus patched schema, RLS, and storage foundation.

**Plan:** Use a mock repository locally and backend-only service-role REST reads for real authorization; create one full Supabase migration. Defer reset because patch §30 places it on Day 5.

**Files touched:** `backend/main.py`, `backend/auth.py`, `backend/config.py`, `backend/db.py`, `backend/events.py`, `supabase/config.toml`, `supabase/migrations/20260726010600_initial_schema.sql`, `.env.example`, `.github/workflows/ci.yml` (created), `.gitignore` (modified).

**Generated:** Health/demo endpoints, JWT dependencies, structured WebSocket hub, service-role reader, UUID schema/enums, child `store_id`s, profile trigger, buckets, helper/RLS policies, demo seed, and Python 3.11 CI.

**Tests written first:** Existing three HTTP/WebSocket contract tests.

**Run results:**
- Run 1: FAILED — tests could not import `main` after it existed.
  → Cause: pytest import root was `backend/tests`.
  → Fix: added `tests/conftest.py` bootstrap; `uvicorn main:app` stays direct.
- Run 2: PASSED — `MOCK_MODE=true .venv/bin/pytest tests` — 3 passed, 0 failed.

**Self-review:** Service-role access remains backend-only; scoped tables use direct `store_id` for RLS.

**Time:** ~12 minutes. **Commit:** `edf9d23` build milestone 1 foundation.
---

### [2026-07-26 01:08 IST] Milestone 1 · live Agent Terminal and Supabase browser shell

**Goal:** Replace terminal replay and password screen with public-demo, WebSocket, and Supabase browser behavior.

**Plan:** Retain semantic tokens but use `.dark`; add capped exponential backoff and Supabase OAuth/magic-link patterns.

**Files touched:** `frontend/components/AgentTerminal.tsx` (rewritten), `ThemeLangControls.tsx`, `app/globals.css`, `app/page.tsx`, `components/AppShell.tsx`, store pages, `app/login/page.tsx`, `tailwind.config.ts` (modified); Supabase client/server files, middleware, auth callback, `lib/constants.ts` (created); package manifest and lockfile (modified).

**Generated:** Live terminal, canonical demo UUID links, semantic Tailwind mapping, session refresh, private-route guard, OAuth callback, Google button, and magic-link form.

**Tests written first:** Existing WebSocket smoke test verifies terminal protocol; typecheck verifies client compile.

**Run results:**
- Run 1: FAILED — `npm run typecheck` — incoming event type omitted `agent`.
  → Cause: renderer type missed protocol field.
  → Fix: restored `agent` to event type.
- Run 2: PASSED — `npm run typecheck` — no errors.
- Run 3: PASSED — `npm run build` — production build completed, including middleware and callback.

**Self-review:** Browser code uses only public keys and reports missing Supabase variables; legacy mock content is outside Day 1 scope.

**Time:** ~10 minutes. **Commit:** `edf9d23` build milestone 1 foundation.
---

### [2026-07-26 01:11 IST] Milestone 1 · local boot and live-stream verification

**Goal:** Verify the frontend and backend connect through the actual WebSocket and record the migration limitation.

**Plan:** Boot both servers, inspect the public demo in the local browser, normalize supplied contract filenames, and never fabricate remote migration output.

**Files touched:** `AGENTS.md`, `SPEC.md`, `SPEC_PATCH_SUPABASE.md`, `DESIGN.md` (renamed only; unchanged content), `docs/codex-log.md` (modified).

**Generated:** Observed Hindi startup log and `Live` connection chip from FastAPI in the public demo.

**Tests written first:** `test_ws_smoke.py` verifies event shape; browser inspection verifies rendering over a live socket.

**Run results:**
- Run 1: PASSED — `MOCK_MODE=true .venv/bin/pytest tests` — 3 passed, 0 failed.
- Run 2: PASSED — Uvicorn booted locally on port 8000.
- Run 3: PASSED — Next.js booted on port 3000; browser found one exact Hindi startup message and one `Live` chip.
- Run 4: BLOCKED EXTERNALLY — `supabase --version` — command not found.
  → Cause: Supabase CLI and linked project credentials are unavailable.
  → Deferred: `supabase login`, `supabase link --project-ref <ref>`, then `supabase db push` before deployment.

**Self-review:** No secrets were used. Provider enablement and redirect URLs are external Supabase dashboard tasks; no intake pipeline work started.

**Time:** ~8 minutes. **Commit:** `edf9d23` build milestone 1 foundation.
---

### [2026-07-26 01:16 IST] Milestone 1 · self-review correction

**Goal:** Confirm Milestone 1 fulfills the logged-review display requirement before the self-review commit.

**Plan:** Re-read the frontend diff and replace the inherited static `/codex-log` mock with server-side reading of the actual markdown file; retain the existing terminal-like, phone-safe presentation.

**Files touched:** `frontend/app/codex-log/page.tsx` (rewritten: reads `docs/codex-log.md`), `frontend/app/globals.css` (modified: readable wrapped markdown panel), `docs/codex-log.md` (modified).

**Generated:** Dynamic `/codex-log` rendering of the actual continuously maintained build log.

**Tests written first:** Existing production build exercises the server route; rerun follows this correction.

**Run results:**
- Run 1: PASSED — `npm run build` — the dynamic `/codex-log` route compiled in the
  production build.
- Run 2: PASSED — `MOCK_MODE=true .venv/bin/pytest tests` — 3 passed, 0 failed.
- Run 3: FOUND DURING LIVE REVIEW — Uvicorn showed redundant sockets because the
  closed floating launcher mounted a connection beside the embedded terminal.
  → Cause: the terminal effect ran even while a non-embedded popover was closed.
  → Fix: the launcher now marks itself offline and skips connecting until opened.
- Run 4: PASSED — `npm run typecheck && npm run build` — no TypeScript errors and
  all production routes compiled.
- Run 5: PASSED — `MOCK_MODE=true .venv/bin/pytest tests` — 3 passed, 0 failed.

**Self-review:** This closes the remaining inherited-prototype mismatch and removes
the redundant closed-launcher connection. The markdown is rendered as text rather than
a full Markdown parser to avoid adding unneeded rendering dependencies in Day 1.

**Time:** ~3 minutes. **Commit:** `edf9d23` build milestone 1 foundation.
---

### [2026-07-26 01:19 IST] Milestone 1 · log and commit reconciliation

**Goal:** Reconcile the continuously written build log with the completed self-review commit.

**Plan:** Record the actual implementation commit hash after it exists; no implementation files change.

**Files touched:** `docs/codex-log.md` (modified: commit references and outcome table).

**Generated:** Final, git-reconcilable Milestone 1 commit references.

**Tests written first:** No code changed; prior final run remains 3 pytest passes plus a successful frontend production build.

**Run results:**
- Run 1: PASSED — `git log --oneline -3` confirms `edf9d23` follows the standalone plan commit `ff69528`.

**Self-review:** This documentation-only commit preserves the required plan → implementation → self-review history without inventing a commit hash before it existed.

**Time:** ~1 minute. **Commit:** pending log-reconciliation commit.
---

## Milestone 1 Summary

**Shipped:** Next.js 14/Tailwind strict foundation with semantic CSS variables and `.dark` mode; FastAPI health/demo/WebSocket service; authorization boundary; public demo seed and full Supabase schema/RLS/storage migration; Supabase browser session scaffolding; tests and Python 3.11 CI.

**Deferred:** Milestone 2 intake/pipeline, Day 5 demo reset, provider dashboard setup, and remote migration application because CLI/project are unavailable.

**Cumulative tests:** 3 passed, 0 failed (`MOCK_MODE=true`); frontend typecheck and production build pass.

**Open risks:** Apply migration to a real Supabase project before database validation; local test runner is Python 3.14 while CI is pinned to 3.11.

---
### [2026-07-26 01:29 IST] Milestone 2 · intake pipeline plan

**Goal:** Specify the narrow Day 2 intake implementation before creating pipeline code.

**Plan:** Build pure CSV normalization first, then mock-safe router infrastructure, then khaata/invoice orchestration with evidence references and bilingual log events. Fixtures will be marked PLACEHOLDER because `sample_data/` is absent.

**Files touched:** `PLAN.md` (modified: detailed Milestone 2 steps and file list), `docs/codex-log.md` (modified: this planning entry), `frontend/.env` (modified locally and ignored: supplied Supabase URL plus local API/WS defaults).

**Generated:** A test-first implementation sequence covering parser edge cases, router failures, vision fixture provenance, and intake-agent dispatch.

**Tests written first:** Scheduled `test_csv_parser.py`, `test_router_mock.py`, and `test_intake_agent.py`; none exist yet because this work unit is the required plan.

**Run results:**
- Run 1: PASSED — verified backend `.env` is populated without reading its values; `frontend/.env` was empty and now contains the user-supplied Supabase URL without an anonymous key.
- Run 2: PASSED — `sample_data/` does not exist, so real vision recordings cannot be honestly claimed at plan time.

**Self-review:** The plan deliberately excludes the uploads endpoint and Storage URL helper: patch §30 assigns Storage work to Day 2 broadly, but the explicit scope is CSV/router/vision intake and says stop at extracted entries. The ambiguity is recorded.

**Time:** ~8 minutes. **Commit:** `1281749` plan milestone 2 intake pipeline.

---
### [2026-07-26 01:31 IST] Milestone 2 · parser, router, and intake contract tests

**Goal:** Define the Day 2 behavior before creating parser, router, or agent modules.

**Plan:** Use pure fixtures and injected fakes so all tests run with `MOCK_MODE=true`.
Cover mobile-payment CSV header variants, malformed inputs, monetary integer integrity,
router fixture/error behavior, and an end-to-end in-memory demo intake write.

**Files touched:** `backend/tests/test_csv_parser.py` (created),
`backend/tests/test_router_mock.py` (created), `backend/tests/test_intake_agent.py`
(created), `docs/codex-log.md` (modified: opened this work-unit entry).

**Generated:** Pending tests for all requested CSV cases, routing table/fixture parsing,
retry failure, khaata/invoice evidence preservation, and bilingual progress events.

**Tests written first:** Parser tests cover PhonePe, GPay, Paytm/bank, Hindi headers,
empty input, malformed rows, debit/credit split columns, and `amount_paise` integer
types. Router tests cover mock fixture loading, fenced JSON parsing, missing fixture,
and one retry. Intake tests require demo-store extraction rows and event text.

**Run results:**
- Run 1: FAILED — `MOCK_MODE=true .venv/bin/pytest tests/test_csv_parser.py
  tests/test_router_mock.py tests/test_intake_agent.py` — collection raised missing
  `intake`, `model_router`, and `agents` modules.
  → Cause: application modules do not exist yet, as intended by the test-first flow.
  → Fix: create the typed parser, router, fixtures, and intake-agent modules next.
- Run 2: FAILED — `test_hindi_headers_are_detected` — parser returned no rows for
  `तारीख, नाम, राशि, यूपीआई रेफ`.
  → Cause: the header normalizer's ASCII-oriented regex stripped Devanagari combining
  marks, so the Hindi synonym could not match.
  → Fix: preserve Unicode mark categories (`Mn`/`Mc`) while removing punctuation.
- Run 3: FAILED — `test_hindi_headers_are_detected` — amount parsed but
  `party_name` was `None`.
  → Cause: the synonym list included Hindi monetary/date/ref labels but omitted the
  common Hindi party header `नाम`.
  → Fix: added `नाम` to party header synonyms.
- Run 4: PASSED — focused Day 2 suite — 14 passed, 0 failed after the vocabulary fix.
- Run 5: FAILED — `test_each_router_call_is_handed_to_model_call_persistence` —
  `model_router` lacked `_persist_model_call`.
  → Cause: in-memory telemetry existed but was not yet handed to the Supabase
  `model_calls` REST table.
  → Fix: added best-effort service-role persistence after every call while retaining
  local telemetry as the no-credential/mock fallback.
- Run 6: PASSED — `MOCK_MODE=true .venv/bin/pytest tests/test_router_mock.py` —
  6 passed, 0 failed.
- Run 7: PASSED — `MOCK_MODE=true .venv/bin/pytest tests` — 19 passed, 0 failed
  (one third-party FastAPI TestClient deprecation warning).
- Run 8: PASSED — `npm run typecheck && npm run build` in `frontend/` — typecheck
  and production build completed.
- Run 9: FAILED — `rg ... backend` while already inside `backend/` — path lookup
  failed because the command accidentally prefixed the current directory.
  → Cause: incorrect review command path, not application code.
  → Fix: reran the scoped checks from the correct directory; the only OpenAI import
  is `model_router.py`, and there are no `float(` conversions in intake or agents.
- Run 10: FAILED — `test_unsupported_intake_kind_is_not_misrouted_to_invoice` — a
  `voice_note` was treated as an invoice.
  → Cause: the initial dispatch used invoice as a catch-all `else` route.
  → Fix: replaced it with an explicit `khaata_photo`/`invoice_image` map and a typed
  unsupported-kind error.
- Run 11: PASSED — `MOCK_MODE=true .venv/bin/pytest tests` — 20 passed, 0 failed
  (one third-party FastAPI TestClient deprecation warning).

**Self-review:** Parser tests reject float monetary output but allow confidence as a
non-money scalar. The invoice prompt has no verbatim text in §7.1, so tests assert the
published JSON schema and evidence semantics rather than inventing a hidden prompt.

**Time:** ~10 minutes. **Commit:** `8c2fae3` milestone 2: intake pipeline (self-reviewed).

---
### [2026-07-26 01:39 IST] Milestone 2 · intake implementation and self-review

**Goal:** Ship the Day 2 CSV and vision extraction paths with safe model routing,
source provenance, and demo-safe fixtures.

**Plan:** Keep CSV entirely standard-library and use `Decimal` for paise conversion;
use a single lazy OpenAI import in the router. For database persistence, send
telemetry through the service-role REST endpoint only when credentials exist and keep
an in-memory record for isolated mock tests. Rejected live fixture recording because
there are no source images in `sample_data/`.

**Files touched:** `backend/intake/__init__.py` (created),
`backend/intake/types.py` (created: immutable extraction draft),
`backend/intake/csv_parser.py` (created: header/datetime/currency parser),
`backend/model_router.py` (created: routing, retries, fixtures, telemetry),
`backend/agents/__init__.py` (created), `backend/agents/intake_agent.py` (created:
CSV and vision dispatch plus WebSocket adapter), `backend/pyproject.toml` (modified:
declared OpenAI SDK), `backend/tests/test_csv_parser.py`,
`backend/tests/test_router_mock.py`, `backend/tests/test_intake_agent.py` (created),
`sample_data/fixtures/vision_khaata.json`, `sample_data/fixtures/vision_invoice.json`,
`sample_data/fixtures/README.md` (created: PLACEHOLDER provenance), and
`docs/codex-log.md` (modified).

**Generated:** `parse_csv_text`, `ExtractedEntryDraft`, `route`, `RouterError`,
fenced-JSON parsing, route telemetry and best-effort `model_calls` persistence,
verbatim khaata prompt, invoice prompt, `IntakeAgent`, and `websocket_emitter`.
Fixtures produce source-referenced demo-store extraction drafts for khaata and
invoices; CSV produces deterministic drafts at confidence 1.0.

**Tests written first:** `test_csv_parser.py`, `test_router_mock.py`, and
`test_intake_agent.py`; 20 backend tests now cover the stated formats, malformed and
empty files, Hindi headers, no-float monetary output, router mock/failure/retry/
telemetry behavior, source references, integer paise, and bilingual WebSocket events.

**Run results:**
- Run 1: PASSED — installed the declared `openai` package in the ignored local
  virtual environment; no live API call was attempted.
- Run 2: PASSED — backend test suite: 20 passed, 0 failed.
- Run 3: PASSED — frontend typecheck and production build.
- Run 4: PASSED — after the telemetry retry review correction, backend suite:
  20 passed, 0 failed.

**Self-review:** Re-read parser conversion and vision transformation to confirm every
amount crosses through `Decimal` then `int` paise; confidence is deliberately the
only floating scalar. Re-read import boundaries: OpenAI is imported lazily only in
`model_router.py`. The router has a 30-second provider timeout and one retry; the
separate telemetry write has a bounded 5-second timeout and one retry, so telemetry
cannot fail extraction. Deferred actual upload/source-document endpoints and physical
Supabase `extracted_entries` writes because the requested Day 2 scope stops at intake
outputs and no upload contract was included. The invoice system prompt is a documented
schema-aligned interpretation because §7.1 only supplies a verbatim khaata prompt.

**Time:** ~10 minutes. **Commit:** `8c2fae3` milestone 2: intake pipeline (self-reviewed).

---
## Milestone 2 Summary

**Shipped:** Pure Python CSV parsing for UPI and bank exports; mock-safe multi-model
router with timeout/retry/telemetry; khaata and invoice intake orchestration;
source-row evidence references; integer-paise conversion; bilingual structured
WebSocket event adapter; and mock-mode test coverage/CI compatibility.

**PLACEHOLDER:** `sample_data/fixtures/vision_khaata.json` and
`sample_data/fixtures/vision_invoice.json`. The repository had no sample images, so
they were schema-valid hand-authored fixtures, explicitly labelled for later live
re-recording. No model call was claimed or performed.

**Deferred:** Upload and source-document API, direct persistence of intake output to
the remote `extracted_entries` table, Storage signed URLs, voice/transcription,
reconciliation, and all Milestone 3 work.

**Cumulative tests:** 20 passed, 0 failed (`MOCK_MODE=true`); frontend typecheck and
production build pass.

**Open risks:** A browser anonymous key still needs to be placed in the ignored
`frontend/.env` from the Supabase dashboard; a real project needs its migration
applied and service-role credentials configured before remote telemetry/extraction
persistence can be verified. The local runner is Python 3.14 while CI targets 3.11.

---
### [2026-07-26 01:49 IST] Milestone 2.5 · integration audit and sample-data plan

**Goal:** Make every existing Milestone 1–2 seam executable and replace absent demo
artifacts with reproducible, ground-truthed samples before starting reconciliation.

**Plan:** Test contracts at their boundaries, use the patched Supabase/Postgres model
as the database source of truth, and generate artifacts from a single deterministic
data definition. Do not pretend a local SQLite/SQLAlchemy check validates a Supabase
migration: if a local Postgres/Supabase runtime is unavailable, record the blocker
after attempting the intended check.

**Files touched:** `PLAN.md` (modified: detailed Milestone 2.5 steps and file list),
`docs/codex-log.md` (modified: planning table and entry).

**Generated:** Audit strategy for imports, schemas, environment variables, design
tokens, migration application, app entrypoints, generated image/CSV data, and fixture
provenance.

**Tests written first:** Scheduled `backend/tests/test_integration_audit.py` before
any seam fix; it will contain column/fixture/event/environment/design regression
checks. Sample-data tests will be added before the generator implementation.

**Run results:**
- Run 1: PASSED — reread the current `AGENTS.md`, `SPEC.md`,
  `SPEC_PATCH_SUPABASE.md`, and `DESIGN.md`; the patch's Postgres/Supabase contract
  overrides the original SQLite/SQLAlchemy wording.

**Self-review:** The user explicitly requires a fresh database migration check but
the patched repository contains SQL migrations, not SQLAlchemy models. The plan keeps
that conflict visible and will neither invent models nor silently weaken the check.

**Time:** ~8 minutes. **Commit:** `9cea175` plan milestone 2.5 integration audit.

---
### [2026-07-26 01:52 IST] Milestone 2.5 · seam and sample-data tests

**Goal:** Express the cross-file and generated-artifact contract as failing checks
before modifying implementation or sample files.

**Plan:** Start with migration/draft, fixture/agent, frontend event/environment/design,
backend import graph, and generator output checks. Separate audit-harness defects from
real product seams so only the latter drive product changes.

**Files touched:** `backend/tests/test_integration_audit.py` (created),
`backend/tests/test_sample_data.py` (created), `docs/codex-log.md` (modified: live
test results).

**Generated:** Eight initial audit tests covering imports, database fields, fixture
schema, events, environment documentation, token/font rules, import cycles, and all
required generated demo artifacts.

**Tests written first:** `test_extraction_draft_fields_fit_the_postgres_table`,
`test_all_runtime_environment_reads_are_documented`,
`test_backend_local_import_graph_has_no_cycles`, and
`test_generator_creates_the_specified_ground_truthed_artifacts`, alongside the
passing seam checks.

**Run results:**
- Run 1: FAILED — focused audit suite: 4 failed, 4 passed.
  → Product seam: `ExtractedEntryDraft.upi_ref` has no matching
  `extracted_entries` migration column, so deterministic UPI evidence cannot persist.
  → Product fix: add a nullable `upi_ref` column to the migration and include it in
  the eventual persistence contract.
  → Audit-harness issue: environment/import graph scans traversed ignored
  `backend/.venv`, incorrectly treating installed packages and their process
  environment reads as project code.
  → Harness fix: exclude dot-directories before evaluating project modules.
  → Expected test-first absence: `sample_data/generate.py` does not exist yet.
  → Next: implement the reproducible generator after checking Pillow/font tooling.

**Self-review:** The first seam test caught a real schema drift. The other two audit
failures are test-harness scope bugs, not grounds to add unrelated environment entries
or inspect virtualenv code.

**Time:** ~8 minutes. **Commit:** `7a9e3d8` milestone 2.5: audit and sample data (self-reviewed).

---
### [2026-07-26 01:57 IST] Milestone 2.5 · live vision fixture recording attempt

**Goal:** Replace PLACEHOLDER vision fixtures with one real extraction run per
generated vision prompt, only because a locally configured API key appeared present.

**Plan:** Load the ignored backend environment without printing it, send only
`khaata_page_1.jpg` and `gupta_inv_231.jpg` through `model_router.route`, and write
returned JSON only if both calls succeed. The router's retry policy remains active.

**Files touched:** `docs/codex-log.md` (modified: failure recorded before fallback).

**Generated:** No fixture data; the live recorder intentionally writes only after a
successful response.

**Tests written first:** Existing router fixture and intake tests protect the fallback
shape; a ground-truth fixture regression test follows before replacement JSON.

**Run results:**
- Run 1: FAILED — `vision_khaata` live recording returned OpenAI HTTP 401 twice and
  `RouterError` after the router retry.
  → Cause: the local `OPENAI_API_KEY` is the documented placeholder, not a usable key.
  → Fix: do not retry manually or claim a live fixture. Generate exact-schema,
  ground-truth-aligned PLACEHOLDER fixtures and retain their provenance label.

**Self-review:** This was an honest attempted recording, not a fabricated result. The
provider safely rejected the placeholder key; no image extraction result was written.

**Time:** ~2 minutes. **Commit:** `7a9e3d8` milestone 2.5: audit and sample data (self-reviewed).

---
### [2026-07-26 02:11 IST] Milestone 2.5 · audit fixes and sample-data self-review

**Goal:** Close the user-verified audit/sample-data milestone without starting
reconciliation work.

**Plan:** Fix only seams proven by the new checks: make UPI references persistable,
validate the demo route on the frontend with Zod, generate reproducible assets with an
open-licensed font, and align fallback fixtures to the source manifest.

**Files touched:** `supabase/migrations/20260726020000_add_extracted_entry_upi_ref.sql`
(created), `backend/pyproject.toml` (modified: Pillow),
`backend/tests/test_integration_audit.py`, `backend/tests/test_sample_data.py`
(created), `frontend/lib/api.ts` (created), `frontend/app/page.tsx` (modified:
validated demo-store call), `sample_data/generate.py`, `GROUND_TRUTH.md`, generated
images/CSV/notice, `sample_data/fonts/Kalam-Regular.ttf`, `sample_data/fonts/OFL.txt`,
and fixture JSON/metadata (created or modified), `docs/codex-log.md` (modified).

**Generated:** Deterministic PIL assets, 60-row PhonePe export, ground-truth manifest,
real migration for `upi_ref`, Zod response schema for `POST /api/stores/demo`, and
auditable placeholder fixture rows for all eight khaata entries plus written total.

**Tests written first:** Audit and generator tests preceded implementation; added
fixture-ground-truth and frontend-Zod seam regressions after their respective missing
contracts were observed.

**Run results:**
- Run 1: PASSED — corrected audit suite: 7 passed after the `upi_ref` migration and
  project-source scoping fixes.
- Run 2: FAILED — ground-truth fixture regression found the prior khaata fixture had
  one row rather than the generated page's eight financial rows plus written total.
  → Fix: regenerated exact-schema PLACEHOLDER fixture values from `GROUND_TRUTH.md`.
- Run 3: FAILED — frontend route seam had no `lib/api.ts`/Zod schema for the backend
  demo response.
  → Fix: added `loadDemoStore` with a strict `store_id`/`is_public`/`is_demo` schema
  and wired the landing action through it, retaining offline-safe demo navigation.
- Run 4: PASSED — audit plus generator suite: 9 passed, 0 failed.
- Run 5: PASSED — FastAPI booted on port 8011 and `/api/health` returned 200;
  Next.js booted on port 3011 and `/` returned 200. Both local audit servers stopped
  cleanly afterward.
- Run 6: BLOCKED/DEFERRED — fresh local Supabase migration execution. The CLI was
  available; Docker Desktop initially was not running, then image downloads began
  after it was launched. The stack was not ready before the user directed Milestone 3,
  so no migration application or table-insert result is claimed.
- Run 7: PASSED — `MOCK_MODE=true .venv/bin/pytest tests` — 30 passed, 0 failed
  (one third-party FastAPI TestClient deprecation warning); `npm run typecheck &&
  npm run build` passed.

**Self-review:** The generator output was visually inspected: the page contains all
eight bilingual handwritten rows, visible ₹18,930 written total, light paper noise,
and slight rotation. `engine/` and `risk.py` do not exist yet (Milestone 3 scope), so
the no-model grep is vacuously clean rather than a substitute for the forthcoming
engine guard. The fresh-local Supabase apply remains the only audit item not completed
in this session; the original request's “SQLAlchemy models” wording conflicts with the
patch's SQL-only Supabase architecture, so no fabricated models were added.

**Time:** ~22 minutes. **Commit:** `7a9e3d8` milestone 2.5: audit and sample data (self-reviewed).

---
## Milestone 2.5 Summary

**Shipped:** Executable import/contract/env/design audits, a forward `upi_ref`
migration, frontend demo-response validation, reproducible PIL sample artifacts with
bundled Kalam/OFL, generated ground truth, and fixture values aligned to that truth.

**PLACEHOLDER:** Both vision fixtures remain PLACEHOLDER. A real recording was
attempted exactly once per required path but safely failed because the configured API
key is invalid; no live result is claimed.

**Deferred:** Fresh local Supabase migration application/table-insert smoke due to
the local image pull not finishing before the user directed Milestone 3. Its original
SQLAlchemy-model phrasing is also superseded by the patch's SQL migration contract.

**Cumulative tests:** 30 passed, 0 failed in `MOCK_MODE=true`; frontend typecheck and
production build pass.

**Open risks:** Replace the local placeholder OpenAI key to re-record vision fixtures;
complete the local Supabase startup then run the real migration/insert smoke before
deployment validation.
