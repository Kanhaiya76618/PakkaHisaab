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

Build the document upload path, Supabase Storage helpers, CSV parser, immutable
extractions, mock router fixtures, and intake-agent events. Add parser and router
failure-path tests before implementation.

## Milestone 3 — reconciliation engine and deterministic tests (Day 3)

Implement normalization, matching rules, anomaly detection, ledger/match writes, and
the money/no-model guard tests. Seed the four deterministic exception scenarios.

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
