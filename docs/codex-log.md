# Codex build log

| Date | Milestone | Task | Outcome | Fix cycles | Commit |
|------|-----------|------|---------|-----------|--------|
| 2026-07-26 | 1 | Contract intake and full-project plan | Complete | 0 | ff69528 |
| 2026-07-26 | 1 | Day 1 implementation and verification | Complete | 4 | edf9d23 |

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

**Time:** ~8 minutes. **Commit:** pending plan commit.
