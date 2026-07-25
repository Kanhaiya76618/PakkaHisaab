# PakkaHisaab implementation plan

This plan follows `AGENTS.md`, `SPEC.md`, `SPEC_PATCH_SUPABASE.md`, and
`DESIGN.md`, in that precedence order. The Supabase patch overrides the original
SQLite/no-auth assumptions; the public demo remains accessible without a session.

## Milestone 1 — foundation, public demo, and live agent transport (Day 1)

**Outcome:** a Supabase-ready monorepo where the public demo page can connect to
FastAPI and receive a structured WebSocket log event. This milestone stops before
the intake pipeline.

1. Normalize the contract filenames to the required uppercase names without changing
   their contents, add a comprehensive `.env.example`, and replace the earlier
   frontend-only plan with this roadmap.
2. Write API and WebSocket smoke tests first. They cover `/api/health`, anonymous
   access to the seeded demo store, private-store rejection, and an agent-log event
   with the required bilingual schema.
3. Add `supabase/migrations/` with the initial Postgres migration: extensions and
   enums, all tables and direct `store_id` relationships, profile trigger, public
   demo-store seed row, storage buckets, RLS enablement, and the helper/policies
   required by the patch. The scheduled demo reset remains Milestone 5, per §30.
4. Scaffold `backend/` as Python 3.11 FastAPI with settings, Supabase service-role
   store lookup, `current_user`, `authorize_store`, a connection manager, health
   route, demo-store route, and the agent-log WebSocket route.
5. Wire the existing Next.js 14 app to the public demo API and WebSocket. Replace
   replay-only terminal data with streamed events plus visible reconnect backoff,
   while preserving `DESIGN.md` semantic tokens, Hindi fallback, and reduced-motion
   behavior.
6. Add the GitHub Actions pytest workflow, run the available tests with
   `MOCK_MODE=true`, type-check/build the frontend, and self-review the diff.

**Milestone 1 planned files**

- `AGENTS.md`, `SPEC.md`, `SPEC_PATCH_SUPABASE.md`, `DESIGN.md` (canonical contract
  filenames; contents unchanged)
- `PLAN.md` (this roadmap)
- `.env.example`, `.gitignore`, `docs/codex-log.md`
- `supabase/config.toml`, `supabase/migrations/202607260001_initial_schema.sql`
- `backend/pyproject.toml`, `backend/main.py`, `backend/config.py`, `backend/auth.py`,
  `backend/db.py`, `backend/events.py`, `backend/routes/demo.py`,
  `backend/tests/test_authz_api.py`, `backend/tests/test_ws_smoke.py`
- `.github/workflows/ci.yml`
- `frontend/lib/api.ts`, `frontend/lib/realtime.ts`,
  `frontend/components/AgentTerminal.tsx`, `frontend/app/store/[id]/hisaab/page.tsx`,
  `frontend/.env.example`, and only the supporting frontend files required to expose
  the live demo route.

## Milestone 2 — deterministic intake and source preservation (Day 2)

**Outcome:** CSV, khaata, and invoice intake paths produce immutable
`extracted_entries`-shaped records for the public demo in `MOCK_MODE=true`, with
source references, deterministic paise conversion, router fallbacks, and streamed
bilingual agent progress. This milestone stops before reconciliation, uploads API,
Storage signed URLs, voice, and exception work.

1. Verify the locally supplied environment files without printing or committing any
   values. Use `MOCK_MODE=true` for all runnable tests; only record live vision
   fixtures if sample images and an API key are both available.
2. Write `test_csv_parser.py` first for PhonePe/GPay/Paytm/bank headers, Hindi
   headers, empty input, malformed rows, debit/credit split rows, integer-paise
   amounts, and a guard proving the parser does not leak float amounts into entries.
3. Implement `backend/intake/csv_parser.py` as pure standard-library Python: normalize
   header synonyms, parse decimal currency with `Decimal`, select amount/debit/credit,
   parse common dates, and return typed extraction records with confidence `1.0` and
   `deterministic_parser` provenance.
4. Write `test_router_mock.py` first for routing-table coverage, mocked fixture
   loading, defensive JSON fence stripping, missing/malformed fixture failures, and
   a non-mock retry/final-`RouterError` path with `model_calls` telemetry.
5. Implement `backend/model_router.py` as the sole OpenAI import location. Add the
   §6 routing table, price/call telemetry interface, 30-second timeout, one retry,
   typed `RouterError`, fixture lookup in `sample_data/fixtures/`, and defensive JSON
   object parsing. Do not add OpenAI imports elsewhere.
6. Write intake-agent tests before its implementation, then add
   `backend/agents/intake_agent.py`: dispatch CSV/khaata/invoice tasks, convert vision
   rupee values to integer paise, preserve `row_ref` as evidence, build
   `extracted_entries` rows, and publish bilingual progress events through the existing
   WebSocket hub.
7. Create clearly labelled placeholder vision fixtures only because the repository has
   no `sample_data/` images at plan time. If images and a usable API key appear during
   implementation, record a real call instead; never silently imply placeholders are
   live-model results.
8. Run all backend tests and the frontend typecheck/build (CI continues to invoke
   pytest). Re-read the diff for forbidden OpenAI imports, float-money leaks, and scope
   creep; update `docs/codex-log.md`, commit the self-review, and stop.

**Milestone 2 planned files**

- `PLAN.md`, `docs/codex-log.md`
- `backend/intake/__init__.py`, `backend/intake/types.py`,
  `backend/intake/csv_parser.py`
- `backend/model_router.py`, `backend/agents/__init__.py`,
  `backend/agents/intake_agent.py`
- `backend/tests/test_csv_parser.py`, `backend/tests/test_router_mock.py`,
  `backend/tests/test_intake_agent.py`
- `sample_data/fixtures/vision_khaata.json`,
  `sample_data/fixtures/vision_invoice.json`, and fixture metadata declaring their
  placeholder provenance
- `backend/pyproject.toml` only if a declared OpenAI package is necessary for the
  non-mock router path; no frontend implementation is planned for this scope.

## Milestone 2.5 — integration audit and reproducible demo artifacts

**Outcome:** cross-file contracts are executable rather than assumed; the repository
contains reproducible, ground-truthed demo images/CSV/notice text and its vision
fixtures are either live-recorded and verified or explicitly ground-truth-aligned
PLACEHOLDERs. This milestone stops before reconciliation-engine implementation.

1. Write audit tests first for Python importability/entrypoints; migration-column vs
   extraction-draft fields; router fixture vs intake parsing; WebSocket event vs
   terminal event schema; environment variables read vs `.env.example`; visual token
   restrictions; and Devanagari fallback chains. Add a test for every newly exposed
   seam rather than relying on a manual inspection.
2. Run the backend and frontend entrypoints, inspect the TypeScript module graph via
   `tsc`/Next build, and use a small import-graph check to report circular or orphaned
   backend modules. Reconcile only actual product modules; test/support modules are
   documented as intentional leaves.
3. Apply the Supabase migration to a fresh local Supabase/Postgres instance if the
   required CLI/container runtime is available, then exercise inserts into every
   application table with a schema-aware SQL smoke test. If the environment cannot
   provide the required Postgres/auth/storage schemas, log the concrete blocker rather
   than claiming a SQLite or partial substitute validates the patched schema.
4. Reconcile every found contract mismatch, including API/frontend schema drift and
   missing env documentation. Preserve the patch's Postgres/Supabase contract rather
   than reintroducing the superseded SQLite/SQLAlchemy design.
5. Add `sample_data/generate.py` using Pillow plus a bundled open-licensed Kalam
   font. It deterministically writes two Hindi/English khaata images, three invoices,
   the exact 60-row PhonePe CSV, and the GST notice. Generate
   `sample_data/GROUND_TRUTH.md` from the same constants and validate its sums,
   duplicate pair, unpaid Gupta invoice, and four personal transactions in tests.
6. Inspect for a usable `OPENAI_API_KEY` without printing it. If present, record each
   vision fixture once against generated images and compare extraction output to ground
   truth; otherwise generate exact-schema PLACEHOLDER fixtures from the same source
   data and state that fact in fixture metadata.
7. Run the full backend suite, frontend typecheck/build, generator idempotence checks,
   static hard-rule sweeps, and a self-review. Maintain `docs/codex-log.md`, commit
   scoped fixes with tests, then stop before Milestone 3.

**Milestone 2.5 planned files**

- `PLAN.md`, `docs/codex-log.md`
- `backend/tests/test_integration_audit.py` and any narrow regression test required
  by a fixed seam; no engine implementation files
- `scripts/` audit helper only if a check cannot be expressed safely in pytest
- `sample_data/generate.py`, `sample_data/GROUND_TRUTH.md`,
  `sample_data/fonts/Kalam-Regular.ttf`, generated `*.jpg`, `july_upi.csv`, and
  `gst_notice_sample.txt`
- `sample_data/fixtures/*.json`, `sample_data/fixtures/README.md` when updated from
  the generated ground truth
- only the backend/frontend/config files directly implicated by a verified seam
  mismatch.

## Integration audit — pre-Milestone 3 contract review

**Outcome:** `docs/audit-m2.md` is a traceable, read-only baseline of every
Milestone 1–2 cross-file seam and deferred obligation. Only after the baseline is
committed will each BREAKS/DRIFT item be fixed with its own regression test and small
commit. The paused Milestone 3 matcher WIP remains outside this audit until close-out.

1. Read-only trace frontend HTTP and WebSocket consumers against FastAPI producers;
   router task/fixture/intake names; database schema/policies against writes;
   environment reads against examples; imports; test coverage; and the `DESIGN.md`
   token/font requirements. Record every finding as source→consumer line references
   and severity, without fixing code in this step.
2. Create `docs/audit-m2.md` with numbered BREAKS, DRIFT, and SMELL findings plus a
   Deferred Register. Include every Milestone 1–2 deferral and explicitly assign the
   patch §30 Day 2 Storage path convention/signed URL work to its appropriate later
   milestone.
3. Commit the audit baseline separately. Then fix BREAKS and DRIFT items in
   source-of-truth order (SPEC, patch, DESIGN), adding a contract test before each
   fix and using one scoped commit per finding/group. Do not weaken existing tests.
4. Run backend tests, frontend typecheck/build, static no-model/no-float/token scans,
   and entrypoint checks. Leave only justified SMELL items and deferred obligations in
   the final audit; summarize counts and stop before resuming Milestone 3.

**Integration audit planned files**

- `PLAN.md`, `docs/codex-log.md`, `docs/audit-m2.md`
- narrow contract regression tests under `backend/tests/` only when an audit finding
  exposes an untested BREAKS seam
- only the producer/consumer files directly named by an audit finding.

## Milestone 3 — deterministic reconciliation engine (Day 3)

**Outcome:** a model-free, deterministic engine reconciles the generated demo inputs
into ledger/match records and produces exactly the four documented exceptions in
`MOCK_MODE=true`. This milestone stops before exception-resolution UI and Evidence
Passport delivery work.

1. Write and commit the complete failing engine suite before engine code:
   `test_money.py` for paise/no-model guards, `test_matchers.py` for every five
   priority rules plus all stated boundaries, and `test_reconciler_e2e.py` that parses
   the generated 2.5 source data and hardcodes the ground-truth ledger/exception
   expectations.
2. Add typed, immutable engine records and data loaders that keep all monetary values
   as integer paise; no model-router, HTTP, or database imports occur in `engine/`.
3. Implement `engine/matchers.py` in strict priority order: exact reference, exact
   amount/date, ±3-day amount window, fuzzy party/amount (0.85 boundary), and
   voice-confirmed. A match always contains its explicit rule and score; split
   payments never merge implicitly.
4. Implement `engine/reconciler.py`: deterministic name/date/value normalization
   (including Devanagari matching), dedupe, matching, ledger/match materialization,
   and anomaly detection for duplicate invoices, khaata written-total arithmetic,
   ≤₹10 mismatches, and explicitly classified personal rows.
5. Add a demo-store reconciliation service/controller that reads a deterministic
   mock fixture repository, calls the engine, returns a typed summary, and publishes
   bilingual progress through the existing store WebSocket hub. Add an API smoke test
   for anonymous demo reconciliation.
6. Run focused rule/e2e/API tests after each implementation increment, then all
   backend tests, static hard-rule sweeps, frontend typecheck/build, and CI-equivalent
   mock suite. Log every red/green cycle and self-review before stopping.

**Milestone 3 planned files**

- `PLAN.md`, `docs/codex-log.md`
- `backend/engine/__init__.py`, `backend/engine/types.py`,
  `backend/engine/matchers.py`, `backend/engine/reconciler.py`, and only deterministic
  fixture/loading helpers required by the engine
- `backend/tests/test_money.py`, `backend/tests/test_matchers.py`,
  `backend/tests/test_reconciler_e2e.py`, and an API regression test for reconciliation
- `backend/main.py` plus a narrow demo reconciliation adapter only after engine tests
  pass; no frontend implementation is planned in this milestone.

## Milestone 4 — exception workflow and Evidence Passport (Day 4)

Add constrained exception actions, authorization checks, resolution flow, and
Evidence Passport API/UI using real document URLs.

## Milestone 5 — risk, exports, storage, and demo reset (Day 5)

Implement deterministic risk scoring, CSV/PDF exports, private signed document URLs,
the demo snapshot/reset SQL job, and the manual demo-reset endpoint/control.

## Milestone 6 — multimodal assistance and scripted schema drift (Day 6)

Add voice intake, Hindi query/TTS, GST notice drafting with evidence constraints, and
the scoped real SQL migration/test replay for the GST column.

## Milestone 7 — evals, authorization sweep, and polish (Day 7)

Create the 15-case evaluation harness and cost dashboard; complete RLS, storage,
reset, and cross-tenant authorization tests; perform the bilingual/accessibility
review and demo break testing.

## Milestone 8 — submission hardening (Days 8–9)

Finalize deployment configuration, README/architecture/Codex log, mobile and fresh
browser checks, demo video assets, uptime-pinger documentation, and final submission
verification.
