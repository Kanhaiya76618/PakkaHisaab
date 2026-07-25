# AGENTS.md — Working agreement for Codex on PakkaHisaab

## Mission

Build PakkaHisaab per the contract files. You are the engineer; the specs are the contract.

**Read in this order before any work:**
1. `AGENTS.md` (this file) — how you work
2. `SPEC.md` — product and backend contract
3. `SPEC_PATCH_SUPABASE.md` — amends SPEC.md. **Where they conflict, the patch wins.**
4. `DESIGN.md` — frontend design contract. Tokens, typography, motion, and UI states are non-negotiable.

**Project:** a multimodal, multi-model AI agent that digitizes an Indian microbusiness's scattered financial records (handwritten khaata photos, invoice images, UPI/bank CSVs, Hindi voice notes), reconciles them into a verified cashbook where every number carries source evidence, and protects the owner with GST notice-risk analysis.

**Deadline:** submission Aug 2, 2026. Hard deadline Aug 3. Scope discipline matters more than feature count.

---

## Workflow (every task, without exception)

1. **PLAN before code.** For each milestone, write or update `PLAN.md` with the step list and file list. **Commit the plan on its own, before writing implementation code.**
2. **TEST-FIRST for backend and engine.** Write the pytest cases from `SPEC.md` §17 and `SPEC_PATCH_SUPABASE.md` §29 before implementing the thing they test.
3. **Run tests after every change.** If red: read the traceback, diagnose, fix, re-run. Log every cycle (see Build logging below).
4. **SELF-REVIEW before ending a milestone.** Re-read your own diff. List risks and smells in `docs/codex-log.md`. Fix the critical ones. Then commit `milestone N: <name> (self-reviewed)`.
5. **STOP at each milestone boundary.** Summarize what you built, what you deferred, and any spec ambiguities you hit. Do not roll into the next milestone unprompted.

---

## Hard rules

- **All money is integer paise.** Floats on amounts are bugs. A test enforces this.
- **`engine/` and `risk.py` are model-free.** No OpenAI calls, no `openai` import, fully deterministic. A test greps for violations.
- **`model_router.py` is the only OpenAI touchpoint.** Every call logs a row to `model_calls`.
- **Every external call:** timeout + one retry + graceful fallback. Demo mode must survive total API failure.
- **No secrets in code.** Env vars only, documented in `.env.example`. Never invent or hardcode a real key.
- **Authorization is not optional.** Every store-scoped route goes through `authorize_store`. RLS policies ship with every table.
- **Commit style:** small, scoped, imperative — "add fuzzy party matcher + boundary tests". Never squash away the plan/test/fix history; judges read it.
- **The frontend follows `DESIGN.md` exactly.** Semantic tokens only (no raw hex in components), Devanagari font fallback chains present, saffron fills carry dark ink text, all four UI states (loading/empty/error/success) implemented per async page.

---

## Build logging (mandatory — this is graded, 15% of the score)

Maintain `docs/codex-log.md` continuously as you work. It is **not** a summary written at the end — write each entry AT THE MOMENT the work happens, before moving to the next step. If the session ended right now, the log must already be accurate and complete.

Keep a running table at the TOP of the file so it reads in 30 seconds:

| Date | Milestone | Task | Outcome | Fix cycles | Commit |
|------|-----------|------|---------|-----------|--------|

Then append one detail block per work unit:

```
---
### [YYYY-MM-DD HH:MM IST] Milestone N · <task name>

**Goal:** one sentence — what this unit of work was meant to achieve.

**Plan:** the approach chosen, and if there was a choice, what was rejected and why.

**Files touched:** `path/one.py` (created), `path/two.tsx` (modified: what changed)

**Generated:** what you actually wrote — components, functions, migrations, tests.
Name them specifically, not "implemented the backend."

**Tests written first:** which test file, which cases, what they assert.

**Run results:**
- Run 1: FAILED — `pytest tests/test_matchers.py::test_fuzzy_window` —
  AssertionError: expected 0.85, got 0.83
  → Cause: rapidfuzz token_set_ratio returns 0-100, not 0-1.
  → Fix: normalized score to /100 in matchers.py:47
- Run 2: PASSED — 14 passed, 0 failed

**Self-review:** what you re-read in your own diff, risks or smells found, which you
fixed and which you consciously deferred (and why).

**Time:** ~N minutes. **Commit:** `<short sha>` <commit message>
---
```

### Logging rules

1. **Every failure gets logged, including the embarrassing ones.** A log with only successes is not credible and reads as fabricated. The fail → diagnose → fix cycles ARE the evidence of agentic work — they are the most valuable content in this file.
2. **Never write an entry for work you did not do.** Never backfill invented timestamps. The log must reconcile with `git log`; a judge who diffs them and finds a mismatch has a reason to discount the whole submission.
3. **Log decisions, not just actions.** When the spec was ambiguous and you chose an interpretation, record the ambiguity and your choice.
4. **Milestone Summary block** at the end of each milestone: what shipped, what was deferred, cumulative test count, open risks.
5. **Commit the log entry alongside the code it describes** — same commit — so the log and history reconcile automatically.
6. `/codex-log` in the app renders this file. Assume a judge reads it on a phone: summary table at top, newest detail entries at the bottom.

---

## Definition of done (whole project)

- Deployed URLs live (Vercel frontend, Render API), tested logged-out and on mobile
- Demo store loads with **zero login** and survives total API failure (`MOCK_MODE`)
- All 4 seeded exceptions reproduce deterministically
- Evidence Passport opens for every ledger entry
- CSV and PDF exports download
- Authorization tests pass: anonymous → demo 200, anonymous → private 403, cross-user 403
- CI green
- `docs/codex-log.md` shows the full plan → tests → fixes → self-review history