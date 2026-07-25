# Pre-Milestone 3 integration audit

**Scope.** This is a read-only audit of the committed Milestone 1–2.5
implementation at `975b3f3`. The unfinished Milestone 3 implementation is
preserved outside this review. `BREAKS` and `DRIFT` items are open until a
subsequent fix commit references the item ID.

## Findings

### A1 — profile schema does not implement the patch

**Severity: DRIFT — fixed in pending A1 commit**

`[SPEC_PATCH_SUPABASE.md:65-83] → [supabase/migrations/20260726010600_initial_schema.sql:22-28,138-146]`

The patch requires `profiles.display_name` and `preferred_lang` (default
`'hi'`, constrained to `hi|en`), with the signup trigger populating
`display_name` from full name or email. The applied migration instead creates
`full_name`, `avatar_url`, and `updated_at`, then writes those old fields.
This is an applied-migration drift and needs a forward migration rather than a
rewrite.

### A2 — anonymous callers can own a private, ownerless store

**Severity: BREAKS — fixed in pending A2 commit**

`[SPEC_PATCH_SUPABASE.md:184-190] → [backend/auth.py:31-37]`

The required gate is `store.is_public or (user_id and
store.owner_user_id == user_id)`. The implementation omits the `user_id`
guard. A malformed private row with `owner_user_id NULL` is therefore returned
to an anonymous request because `None == None`. The current tests cover only
the public demo route and do not exercise this authorization seam.

### A3 — upload UI has no API, Storage write, source-document row, or intake persistence

**Severity: BREAKS**

`[SPEC.md:253-255,354] → [frontend/components/UploadZone.tsx:10-19] → [backend/main.py:25-54] → [backend/agents/intake_agent.py:45-54,93-118]`

The specified multipart `POST /api/stores/{id}/uploads` route does not exist.
The frontend only holds selected files in React state; it never issues a
request. Intake writes only to `InMemoryExtractionRepository`, so its
`ExtractedEntryDraft` records never reach `public.extracted_entries` even
though the table contract exists at
`[supabase/migrations/20260726010600_initial_schema.sql:56-70]`. This breaks
the Day 2 end-to-end intake contract.

### A4 — required storage helper and path convention are absent

**Severity: BREAKS**

`[SPEC_PATCH_SUPABASE.md:197-214,270-276] → [supabase/migrations/20260726010600_initial_schema.sql:42-54,199-207] → [backend/:1]`

The buckets and object RLS policies exist, but there is no backend path helper
implementing `{bucket}/{store_id}/{document_id}.{ext}`, no private signed-URL
helper, and no public demo URL helper. The `source_documents.storage_path`
column is consequently unused. This was explicit Day 2 work and prevents the
Evidence Passport from locating source evidence safely.

### A5 — demo endpoint and rendered demo are disconnected from seeded data

**Severity: BREAKS**

`[SPEC.md:335] → [backend/main.py:31-34] → [supabase/migrations/20260726010600_initial_schema.sql:209-210] → [frontend/app/store/[id]/hisaab/page.tsx:12,21-27]`

`POST /api/stores/demo` returns only a fixed ID. The migration seeds only the
store row; it has no source documents, extracted entries, ledger entries, or
exceptions. The Hisaab screen renders static rupee-valued `demo-data.ts`
instead of the backend response and simulates reconciliation with a timer.
This contradicts the required pre-processed fixture-backed demo and masks the
missing producer/consumer API contract.

### A6 — backend Supabase calls have neither the required explicit timeout nor retry

**Severity: DRIFT**

`[AGENTS.md:39] → [backend/db.py:24-42]` and
`[AGENTS.md:39] → [backend/model_router.py:76-107]`

The service-role store read and `model_calls` insert instantiate `httpx`
clients without an explicit 30-second timeout and have no one-retry fallback.
The router's OpenAI call has retry handling, but its logging/database seam does
not. The contract requires every external call to have timeout, one retry, and
graceful fallback.

### A7 — mock routing coverage is narrower than its routing table

**Severity: SMELL**

`[backend/model_router.py:24-38] → [backend/model_router.py:124-132,153-167]`

Eight task names are routable, but only the two Day 2 vision task names have
fixtures. This does not break current intake calls
(`[backend/agents/intake_agent.py:101-106]`), but future MOCK_MODE tasks raise
`RouterError` rather than returning canned data. The existing test asserts
only the vision subset (`backend/tests/test_router_mock.py:10-12`).

### A8 — the existing integration tests inspect text and mocks, not the live seams

**Severity: SMELL**

`[backend/tests/test_integration_audit.py:112-125] → [backend/main.py:25-54] → [frontend/components/AgentTerminal.tsx:48-55]`

The websocket and frontend API checks search source text; they never run a
frontend client against FastAPI. Likewise, the persistence test monkeypatches
`_persist_model_call` (`backend/tests/test_router_mock.py:25-35`). This allowed
the missing upload and demo-data contracts to pass despite no live producer /
consumer connection.

### A9 — full pytest is not currently green because committed M3 tests import stashed implementation

**Severity: SMELL**

`[backend/tests/test_matchers.py:3-4,backend/tests/test_reconciler_e2e.py:5] → [backend/engine/:1]`

The committed test-first M3 suite imports `engine.matchers` and
`engine.reconciler`, while the unfinished engine implementation is deliberately
preserved outside the audit worktree. Full pytest therefore stops at two
collection errors. This is expected test-first M3 state, not a Milestone 1–2.5
regression; the audit must not delete or weaken those tests.

## Verified seams

- The backend event producer has exactly `agent`, `level`, `message_en`,
  `message_hi`, and `detail` (`backend/events.py:12-17`); the terminal's type
  has the same fields and its level union agrees (`frontend/components/AgentTerminal.tsx:9-11,48-55`).
- CSV drafts include `upi_ref` and the forward migration adds the same column
  (`backend/intake/types.py:9-22` →
  `supabase/migrations/20260726020000_add_extracted_entry_upi_ref.sql:1-7`).
- `can_read_store` / `can_write_store` names agree with every table policy
  (`supabase/migrations/20260726010600_initial_schema.sql:152-195`).
- Every direct runtime environment-variable read is documented in
  `.env.example`; `DATABASE_URL` is configured but not consumed by a database
  client (a non-blocking configuration smell).
- The only `openai` import is lazy and inside `backend/model_router.py:137`.
  No committed `engine/` module exists yet, so it has no model dependency.
- Frontend components use semantic CSS tokens and the Devanagari fallback is
  present; frontend typecheck and production build pass.

## Deferred register

| Item | Required milestone | Evidence / note |
|---|---:|---|
| Multipart uploads, storage path convention, signed/public document URLs, and persistent source/extraction writes | **M2 (overdue; A3/A4)** | Patch §30 Day 2; must be fixed in this audit task. |
| Fixture-backed seeded demo data and replayable demo pipeline | **M2 (overdue; A5)** | SPEC §335; must be fixed in this audit task. |
| Voice recording/upload/transcription | M6 | UI is a timer-only placeholder (`frontend/components/VoiceRecorder.tsx:7-14`). |
| Reconciliation endpoint, deterministic engine, ledger/match/exception persistence | M3 | Tests are committed test-first; implementation is paused. |
| Evidence Passport live source URLs and exception actions | M4 | Current component is static demo presentation. |
| Risk, exports, demo snapshot/reset job and reset button | M5 | Patch §27 and §30 Day 5. |
| GST notice flow, Hindi voice query/TTS, schema-drift replay | M6 | No API implementation. |
| Full auth/RLS/storage/cascade/reset test sweep against local Supabase | M7 | Patch §29; local Supabase verification remains pending. |
| Deployments, uptime pinger, mobile/fresh-browser checks, submission assets | M8 | Patch §22 and project definition of done. |

## Audit execution record

- `MOCK_MODE=true .venv/bin/pytest tests -q` from `backend/` stopped at two
  expected M3 collection errors described in A9.
- An initial command used the frontend working directory with a relative
  backend virtualenv path and failed before pytest started; rerunning from
  `backend/` produced the record above.
- `npm run typecheck` and `npm run build` in `frontend/` passed.
