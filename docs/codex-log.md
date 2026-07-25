# Codex build log

| Date | Milestone | Task | Outcome | Fix cycles | Commit |
|------|-----------|------|---------|-----------|--------|
| 2026-07-26 | 1 | Contract intake and full-project plan | Complete | 0 | pending plan commit |

## Historical context

The two commits before the contract files were supplied (`c5957d5`, `65c0a8c`) contain
an initial frontend prototype. They predate this working agreement and are not
retroactively represented as detailed work blocks; no timestamps, tests, or failures
are being invented for them. Milestone 1 audits and adapts that prototype to the
Supabase/public-demo contract.

---
### [2026-07-26 00:56 IST] Milestone 1 · contract intake and implementation plan

**Goal:** Establish the governing architecture and a complete milestone roadmap before
creating Milestone 1 implementation files.

**Plan:** Read the supplied working agreement, base specification, Supabase patch, and
design contract in order. Preserve the existing frontend prototype, but treat it as
pre-contract work that must be adapted rather than as compliant Milestone 1 output.

**Files touched:** `PLAN.md` (modified: replaced frontend-only scope with the complete
milestone plan and detailed Milestone 1 file list), `docs/codex-log.md` (modified:
added the required summary table and this contemporaneous entry).

**Generated:** Full eight-milestone roadmap, detailed Day 1 sequence, and a complete
Milestone 1 planned-file inventory covering Supabase, FastAPI, tests, CI, and the
live Agent Terminal connection.

**Tests written first:** None; this work unit is planning only. The plan explicitly
requires `backend/tests/test_authz_api.py` and `backend/tests/test_ws_smoke.py` before
the corresponding API/WebSocket implementation.

**Run results:**
- Run 1: PASSED — read `Agents.md`, `Spec.md`, `spec_patch_supabase.md`, and
  `design.md` completely; the Supabase patch was identified as overriding SQLite,
  Alembic, and password-login assumptions.

**Self-review:** Re-read the plan against §18 and patch §30. The main risk is the
earlier password-login prototype conflicting with the patched Google/magic-link flow;
it is explicitly scheduled for replacement during Milestone 1, while the public demo
route remains unauthenticated. The required contract filenames currently differ only
by case and are scheduled for normalization after this plan commit.

**Time:** ~12 minutes. **Commit:** pending plan commit.
---
