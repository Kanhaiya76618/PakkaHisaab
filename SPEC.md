# PakkaHisaab — Complete Build Specification (Codex-Ready)

> **How to use this document:** Place this file in the repo root as `SPEC.md`. Copy Section 19 into a separate `AGENTS.md`. Then instruct Codex: *"Read SPEC.md and AGENTS.md. Produce an implementation plan as PLAN.md, commit it, then execute milestone by milestone. Write tests before marking any milestone complete."*

---

## 1. Project Overview

**Name:** PakkaHisaab
**Tagline:** Five ways in, one truth out.
**One-liner:** A multimodal, multi-model AI agent that digitizes an Indian microbusiness's scattered financial records (handwritten khaata photos, invoice images, UPI/bank CSVs, Hindi voice notes), reconciles them into a verified cashbook where every number carries source evidence, and protects the owner with GST notice-risk analysis and evidence-backed notice replies.

**Hackathon:** ChatGPT Codex India Hackathon 2026 (BlockseBlock). Deadline: Aug 3, 2026 (target submission: Aug 2).
**Theme:** #6 — AI for Bharat Businesses.

**Three product modules (the user journey):**
1. **Digitize** — multimodal intake: photos, PDFs, CSVs, voice, text → structured data.
2. **Reconcile** — deterministic matching engine + exception workflow + Evidence Passport.
3. **Protect** — GST notice risk radar + notice-reply drafter.

**Core trust principle (repeat in UI copy and README):**
> AI reads and reasons; **only code touches the math**. Models extract and explain. Deterministic Python computes every total, match, and balance. The AI never invents a financial fact — every number links to its source via an Evidence Passport.

---

## 2. Judging Context — Non-Negotiables

| Criterion | Weight | What we do |
|---|---|---|
| Technical execution | 50% | Real matching engine, multi-model router, WebSocket agent logs, migrations, test suite |
| Real-world impact | 20% | 2026 UPI-based GST notice wave; MSME digitization |
| Proper use of Codex | 15% | AGENTS.md, committed PLAN.md, Codex-written tests, self-review commits, /codex-log page |
| Creativity | 10% | Evidence Passport, no-model zone, model router cost/quality chart |
| Demo quality | 5% | Seeded demo mode, scripted 3-min video |

**Viability gate (instant disqualification if failed):**
- Deployed URL must open and work with **no login**.
- Demo mode must work even if all external APIs fail (see §11 fallbacks).
- GitHub repo public; commits must match the demo.

---

## 3. Tech Stack

- **Frontend:** Next.js 14+ (App Router), TailwindCSS, Recharts, deployed on **Vercel**.
- **Backend:** Python 3.11, FastAPI, WebSockets, deployed on **Render** (free tier; add a keep-alive ping note in README since free tier sleeps).
- **DB:** SQLite via SQLAlchemy 2.x + Alembic (migrations are a demo feature). Single file DB is fine.
- **AI:** OpenAI APIs — see Model Router (§6). All calls go through one `model_router.py` module. API key via env var `OPENAI_API_KEY`, never committed.
- **Testing:** pytest + pytest-asyncio (backend), Playwright smoke test (frontend, optional).
- **No Docker requirement** for the deployed app (Render buildpacks fine). Local dev may use docker-compose (optional).

---

## 4. Repository Structure

```
pakkahisaab/
├── AGENTS.md                  # Codex working agreement (from §19)
├── SPEC.md                    # this file
├── PLAN.md                    # Codex-generated implementation plan (committed Day 1)
├── README.md                  # setup, architecture diagram, demo links, Codex usage story
├── frontend/                  # Next.js app
│   ├── app/
│   │   ├── page.tsx                 # landing + "Open Demo Store" button
│   │   ├── store/[id]/
│   │   │   ├── digitize/page.tsx    # Module 1
│   │   │   ├── hisaab/page.tsx      # Module 2 (default tab)
│   │   │   ├── kavach/page.tsx      # Module 3
│   │   │   └── evals/page.tsx       # eval dashboard
│   │   └── codex-log/page.tsx       # renders docs/codex-log.md
│   ├── components/
│   │   ├── AgentTerminal.tsx        # slide-out panel, streams WS logs
│   │   ├── EvidencePassport.tsx     # drawer component
│   │   ├── ExceptionCard.tsx
│   │   ├── UploadZone.tsx
│   │   ├── VoiceRecorder.tsx
│   │   ├── RiskRadar.tsx
│   │   └── LangToggle.tsx           # hi/en, stores in localStorage-free state (React state + URL param)
│   └── lib/i18n.ts                  # all UI strings in hi + en
├── backend/
│   ├── main.py                      # FastAPI app, CORS, WS endpoint
│   ├── model_router.py              # §6 — the ONLY file that calls OpenAI
│   ├── agents/
│   │   ├── intake_agent.py          # §7.1
│   │   ├── exception_agent.py       # §7.3
│   │   ├── audit_agent.py           # §7.4
│   │   └── notice_agent.py          # §7.5
│   ├── engine/
│   │   ├── reconciler.py            # §10 — deterministic, NO model calls allowed
│   │   ├── matchers.py              # matching rules
│   │   └── risk.py                  # §14 risk scoring — deterministic
│   ├── db/
│   │   ├── models.py                # §5
│   │   ├── seed.py                  # §11 demo data
│   │   └── migrations/              # Alembic
│   ├── routes/
│   │   ├── uploads.py, transactions.py, exceptions.py,
│   │   ├── query.py, exports.py, evals.py, demo.py
│   ├── evals/
│   │   ├── cases/                   # 15 JSON cases (§12)
│   │   └── runner.py
│   └── tests/                       # §17
├── docs/
│   ├── codex-log.md                 # running log of Codex prompts/plans/reviews
│   └── architecture.md
└── sample_data/                     # demo images, CSVs, audio (committed)
```

---

## 5. Data Model (SQLAlchemy → SQLite)

```sql
-- stores
id TEXT PK, name TEXT, owner_name TEXT, lang TEXT DEFAULT 'hi', created_at

-- source_documents  (every uploaded artifact)
id TEXT PK, store_id FK, kind TEXT CHECK(kind IN
  ('khaata_photo','invoice_image','invoice_pdf','bank_csv','upi_csv',
   'upi_screenshot','voice_note','manual','gst_notice')),
filename TEXT, file_path TEXT, page_no INT NULL,
raw_text TEXT NULL,            -- OCR/transcript output
uploaded_at, processed_at NULL, status TEXT DEFAULT 'pending'

-- extracted_entries  (model output BEFORE reconciliation; immutable)
id TEXT PK, source_document_id FK, entry_type TEXT CHECK(entry_type IN
  ('sale','purchase','payment_in','payment_out','credit_given','credit_received','note')),
party_name TEXT NULL, amount_paise INTEGER,     -- ALWAYS integer paise, never float
currency TEXT DEFAULT 'INR', entry_date DATE NULL,
description TEXT, confidence REAL,               -- 0.0–1.0 from intake agent
extraction_model TEXT,                           -- which model produced this
bbox_or_line_ref TEXT NULL                       -- e.g. "page 1, row 4" for Evidence Passport

-- ledger_entries  (the verified cashbook; created only by reconciler or user confirmation)
id TEXT PK, store_id FK, entry_type TEXT, party_name TEXT,
amount_paise INTEGER, entry_date DATE, description TEXT,
status TEXT CHECK(status IN ('verified','pending_confirmation')),
created_by TEXT CHECK(created_by IN ('reconciler','user')),
created_at

-- matches  (evidence links: which sources support which ledger entry)
id TEXT PK, ledger_entry_id FK, extracted_entry_id FK,
match_rule TEXT,        -- e.g. 'exact_amount_date', 'fuzzy_party_amount', 'voice_confirmed'
match_score REAL

-- exceptions
id TEXT PK, store_id FK, kind TEXT CHECK(kind IN
  ('unmatched_invoice','unmatched_payment','possible_duplicate',
   'amount_mismatch','personal_vs_business','arithmetic_error')),
summary_en TEXT, summary_hi TEXT,
related_extracted_ids TEXT,      -- JSON array
suggested_action TEXT,           -- JSON: {action, params}
status TEXT CHECK(status IN ('open','resolved','dismissed')) DEFAULT 'open',
resolved_at NULL, resolution TEXT NULL

-- model_calls  (powers eval/cost dashboard)
id TEXT PK, task TEXT, model TEXT, input_tokens INT, output_tokens INT,
cost_usd REAL, latency_ms INT, success BOOL, created_at

-- gst_notices
id TEXT PK, store_id FK, source_document_id FK, raw_text TEXT,
flagged_items TEXT,      -- JSON extracted claims
draft_reply TEXT NULL, created_at
```

**Money rule (test-enforced):** all amounts are integer paise. Any float amount anywhere in `engine/` fails CI.

---

## 6. Model Router (`backend/model_router.py`)

The **only** module allowed to import the OpenAI SDK. Everything else calls `route(task, payload)`.

```python
ROUTING_TABLE = {
  # task                     model                 max_tokens  notes
  "vision_khaata":         ("gpt-4o",              2000),  # handwritten Devanagari+numerals
  "vision_invoice":        ("gpt-4o",              1500),
  "vision_upi_screenshot": ("gpt-4o-mini",          500),  # simple structured screens
  "transcribe_hi":         ("whisper-1",           None),  # or gpt-4o-audio if available
  "classify_txn":          ("gpt-4o-mini",          200),  # business/personal/refund/duplicate
  "exception_reasoning":   ("gpt-4o",              1200),
  "notice_draft":          ("gpt-4o",              2500),
  "nl_query":              ("gpt-4o-mini",          800),  # Hindi Q&A over structured data
  "tts_hi":                ("tts-1",               None),  # spoken answers, voice="alloy"
}
```

Requirements:
1. Every call logs a row to `model_calls` (task, model, tokens, cost from a hardcoded price table, latency, success).
2. Every call has a **timeout (30s) and one retry**; on final failure return a typed `RouterError` — callers must degrade gracefully (see §11 fallbacks).
3. All extraction tasks use `response_format={"type":"json_object"}` with a schema in the prompt; parse defensively (strip fences, try/except).
4. A `MOCK_MODE=true` env var makes the router return canned fixtures from `sample_data/fixtures/` — this powers demo-mode reliability and lets tests run without an API key.

---

## 7. Agent Specifications

Agents are Python orchestration classes. Each emits structured log events to the WebSocket bus: `{agent, level, message_en, message_hi, detail?}` so the Agent Terminal can render them live.

### 7.1 Intake Agent
**Input:** a `source_documents` row. **Output:** rows in `extracted_entries`.
- Dispatch by `kind` → router task (`vision_khaata`, `vision_invoice`, `transcribe_hi` then `classify_txn`, CSV → pure-Python parser, no model).
- **CSV parser (no model):** support PhonePe/GPay/Paytm/bank export shapes. Detect columns by header synonyms (`Amount`, `राशि`, `Debit`, `Credit`, `Txn Date`, `UPI Ref`). Normalize to extracted_entries with confidence 1.0.
- Vision prompt (khaata), verbatim system prompt:

```
You are a data-extraction engine for handwritten Indian shop ledgers (khaata).
The image may mix Hindi (Devanagari) and English, with columns like party name,
item, amount, and running totals. Extract EVERY row as JSON:
{"entries":[{"entry_type":"credit_given|payment_in|sale|note",
 "party_name":str|null,"amount_rupees":number|null,"entry_date":"YYYY-MM-DD"|null,
 "description":str,"row_ref":"page P, row N","confidence":0.0-1.0}]}
Rules: 1) NEVER invent amounts — if unreadable, amount_rupees=null and confidence<=0.3.
2) Do not sum or correct arithmetic; extract what is written, including the written total
as entry_type "note" with description "written_total". 3) Output JSON only.
```

- Voice-note prompt (`classify_txn` after transcription): given transcript like *"Ramesh ko ₹2,500 cash diya"*, output one entry `{entry_type:"payment_out", party_name:"Ramesh", amount_rupees:2500, description:transcript, confidence}`.

### 7.2 Reconciler — **NOT an agent. Pure code.** See §10.

### 7.3 Exception Agent
**Input:** reconciler output (unmatched/conflicting sets). **Output:** `exceptions` rows.
- For each anomaly the engine flags, call `exception_reasoning` to produce `summary_en`, `summary_hi`, and a `suggested_action` from a **closed set**: `create_entry`, `merge_duplicates`, `mark_personal`, `adjust_amount`, `ask_user`. The model may only choose+parameterize; it cannot invent new action types (validate against enum, reject otherwise).

### 7.4 Audit Agent
Runs after reconciliation. For every `ledger_entries` row, verifies: (a) ≥1 `matches` link exists or `created_by='user'`; (b) sum of party balances equals engine-computed totals (recompute independently in this agent using the same paise integers — this is a code check, the model only writes the human-readable audit summary). Emits the "Evidence Passport complete: N/N entries sourced" log line — a scripted demo beat.

### 7.5 Notice Agent (Kavach)
**Input:** pasted/uploaded GST notice text. **Steps:**
1. `notice_draft` extraction pass: pull flagged amounts/periods/claims into JSON.
2. Code pass: for each flagged amount, query ledger + matches for supporting evidence within ±3 days and ±₹1 tolerance windows.
3. `notice_draft` drafting pass with this system prompt:

```
You draft a reply to an Indian GST notice on behalf of a small trader. You are given
(a) the notice's flagged items and (b) verified ledger evidence for each item.
For each flagged item write: the department's claim, our records' explanation, and the
attached evidence reference. If evidence is missing, say "records under compilation" —
NEVER fabricate an explanation. Formal, respectful Hindi-English bilingual format.
End with: "This draft is for reference. Please review with a Chartered Accountant
before filing." Output markdown.
```

UI must show the CA disclaimer prominently, not only inside the draft.

---

## 8. API Endpoints (FastAPI)

```
POST /api/stores/demo                 → creates/loads seeded demo store, returns store_id
POST /api/stores/{id}/uploads         → multipart; kind param; returns document_id; kicks intake (background task)
WS   /ws/stores/{id}/agent-log        → streams agent events
POST /api/stores/{id}/reconcile      → runs engine + exception + audit agents; returns summary
GET  /api/stores/{id}/ledger          → ledger + balances by party
GET  /api/stores/{id}/exceptions      → open exceptions
POST /api/exceptions/{id}/resolve     → {action, params} from closed set
GET  /api/ledger-entries/{id}/evidence→ Evidence Passport payload (§9)
POST /api/stores/{id}/query           → {text|audio, lang} → {answer_text, answer_audio_b64?}
GET  /api/stores/{id}/risk            → risk radar payload (§14)
POST /api/stores/{id}/notices         → upload/paste notice → draft reply
GET  /api/stores/{id}/export?fmt=csv|pdf
GET  /api/evals/run                   → runs 15 cases, returns scores (cached 10 min)
GET  /api/model-usage                 → cost/latency/accuracy aggregates for eval page
```

---

## 9. Evidence Passport (the signature feature)

`GET /api/ledger-entries/{id}/evidence` returns:

```json
{
  "ledger_entry": {"amount":"₹4,800.00","party":"Gupta Traders","date":"2026-07-12","type":"purchase"},
  "sources": [
    {"kind":"invoice_image","filename":"gupta_inv_231.jpg","ref":"full page",
     "extracted":{"amount":"₹4,800.00","party":"Gupta Traders","date":"2026-07-12"},
     "confidence":0.94,"model":"gpt-4o","thumbnail_url":"..."},
    {"kind":"upi_csv","filename":"july_upi.csv","ref":"row 41",
     "extracted":{"amount":"₹4,800.00","upi_ref":"617234889912"},
     "confidence":1.0,"model":"deterministic_parser"}
  ],
  "match_rule":"exact_amount_date",
  "match_score":1.0,
  "actions":[{"at":"2026-07-28T14:02:11Z","by":"reconciler","what":"auto-matched"}]
}
```

Frontend `EvidencePassport.tsx`: right-side drawer; shows the ledger number at top, then each source as a card with thumbnail (images), extracted fields vs ledger fields side by side, confidence bar, model badge, and the match rule in plain language ("Matched because amount and date are identical"). Hindi/English per toggle.

---

## 10. Deterministic Reconciliation Engine (`engine/` — model calls forbidden; enforce with a test that greps for `openai` imports)

**Pipeline:** normalize → dedupe → match → detect anomalies → write ledger + matches → return unmatched sets.

**Normalization:** party names → casefold, strip honorifics (ji, bhai, sahab), transliterate Devanagari→Latin (use `indic-transliteration` lib) so "रमेश" == "Ramesh"; dates → ISO; amounts → paise ints.

**Matching rules, applied in strict order (record `match_rule` used):**
1. `exact_ref` — UPI ref / invoice number string match. Score 1.0.
2. `exact_amount_date` — same paise, same date, compatible types (invoice ↔ payment_out). Score 1.0.
3. `amount_within_window` — same paise, date within ±3 days. Score 0.9.
4. `fuzzy_party_amount` — normalized party token-set ratio ≥ 0.85 (rapidfuzz) AND same paise, date ±7 days. Score 0.8.
5. `voice_confirmed` — voice-note entry matching amount ±0 and party fuzzy ≥ 0.85. Score 0.85.

Anything below 0.8 → unmatched → Exception Agent.

**Anomaly detectors (pure code):**
- `possible_duplicate`: two extracted entries, same amount, same party, dates ≤1 day apart, different sources.
- `arithmetic_error`: sum of a khaata page's rows ≠ its extracted `written_total` note (this powers the demo's red-test moment).
- `amount_mismatch`: matched pair differing by ≤ ₹10 (likely OCR digit error) → exception, never auto-corrected.
- `personal_vs_business`: CSV rows whose classify_txn label = personal but appear in business account.

---

## 11. Seeded Demo — "Sharma Kirana Store" (`db/seed.py` + `sample_data/`)

Create realistic committed artifacts (generate images with PIL-rendered "handwriting" font or photograph real staged pages):
- `khaata_page_1.jpg` — 8 rows, mixed Hindi/English, includes a **deliberate arithmetic error**: rows sum to ₹18,730 but written total says ₹18,930.
- `khaata_page_2.jpg` — 6 rows **with a new "GST" column** → triggers schema-drift path (§15).
- 3 invoice images (`gupta_inv_231.jpg` etc.), one being a **near-duplicate** of another (same amount/party, next day).
- `july_upi.csv` — 60 rows, PhonePe export format; includes 4 personal transactions, one payment matching each invoice except one (→ `unmatched_invoice` for ₹4,800).
- `voice_ramesh.m4a` — Hindi audio: "Ramesh ko pachchees sau rupaye cash diye, yaad rakhna."
- `gst_notice_sample.txt` — notice claiming UPI receipts of ₹2,41,000 vs declared ₹1,98,000 for July.

**The 4 seeded exception scenarios (must all reproduce deterministically):**
1. ₹4,800 Gupta Traders invoice with no matching payment (`unmatched_invoice`).
2. Duplicate supplier invoice pair (`possible_duplicate`).
3. Khaata page 1 arithmetic error ₹200 (`arithmetic_error`).
4. ₹15,000 UPI credit classified personal — brother's transfer (`personal_vs_business`).

**Demo-mode reliability rule:** `POST /api/stores/demo` loads everything **pre-processed from fixtures** (extracted_entries already seeded). The "Run pipeline" button in demo mode replays recorded agent-log events with realistic delays via the WebSocket, then live-calls only the cheap final steps. If `MOCK_MODE=true` or any API call fails, everything still completes from fixtures. Judges must never see a spinner die.

---

## 12. Eval Page (Theme-5 flex)

`backend/evals/cases/` — 15 JSON cases, each: `{input_ref, task, expected}`.
- 5 extraction cases (noisy khaata crops → expected entries; score = field-level F1).
- 5 matching cases (synthetic entry sets → expected match pairs; score = pair accuracy).
- 3 classification cases (txn descriptions → business/personal).
- 2 end-to-end cases (mini document sets → expected exception list).

`evals/runner.py` runs all, writes scores + per-case cost from `model_calls`.
Frontend `evals/page.tsx`: overall accuracy per category, a **cost-vs-accuracy scatter** (router model choices), and the headline stat card: "Model router: −X% cost vs all-GPT-4o, −Y pp accuracy" (compute the counterfactual by re-running the 5 extraction cases once with gpt-4o-mini forced and once with gpt-4o forced; cache results in repo as JSON so the page never needs live calls).

---

## 13. Multimodal I/O Details

- **VoiceRecorder.tsx:** MediaRecorder API → webm/m4a → `/uploads?kind=voice_note`. Show live transcript when processed.
- **Hindi Q&A:** `/query` builds a compact structured context (party balances, month totals, open exceptions — max ~2k tokens, **numbers computed by code and injected**, model only phrases the answer) → `nl_query` → optional `tts_hi` → return base64 mp3 → autoplay with a replay button. System prompt must say: *"Answer only from the provided figures. If the figure is not provided, say you don't have it. Never compute new totals."*
- **Language toggle:** every UI string lives in `lib/i18n.ts` as `{en, hi}`. Default `hi` for demo store.

---

## 14. Risk Radar (`engine/risk.py` — deterministic)

Inputs: monthly UPI credits total, monthly declared turnover (user-entered or seeded), thresholds.
Outputs:
- `gap_by_month`: [{month, upi_received, declared, gap, gap_pct}]
- `risk_score` 0–100: weighted — gap_pct (60%), unresolved exceptions count (25%), personal/business ambiguity ratio (15%). Document the formula in the UI ("How is this computed?" expander).
- `warnings`: registration-threshold proximity, month-over-month spike >40%.
Frontend: Recharts bar (received vs declared), gauge for score, warning list. Seeded data must produce score ≈ 68 (Amber) with the July gap visible — matches the sample notice.

---

## 15. Schema-Drift Demo Path (scoped KhaataForge magic)

Trigger: uploading `khaata_page_2.jpg` (has GST column).
1. Intake agent extraction includes unknown field `gst_amount` → drift detector (code) compares against known ledger fields.
2. Agent Terminal logs: "New column detected: GST. Generating migration…"
3. Backend runs a **pre-written but genuinely executed** Alembic migration adding `gst_amount_paise` to ledger_entries; runs pytest subset live (`tests/test_migration_gst.py`) — first run intentionally includes a failing assertion revision (seeded), agent "fixes" by applying the corrected migration, tests pass, terminal goes green.
4. Ledger UI now shows the GST column with page-2 data; page-1 entries show "—".

This must actually execute (real migration, real pytest run streamed to terminal) — but only needs to work for this exact scripted input. Do not generalize.

---

## 16. Exports

- **CSV:** ledger with columns incl. evidence source filenames + match rule.
- **PDF "Month-End Evidence Pack"** (use `reportlab` or `weasyprint`): cover summary, ledger table, exception log with resolutions, per-entry evidence appendix (thumbnails + refs), risk summary. One click, < 10s, works in demo mode.

---

## 17. Testing Requirements (Codex writes these FIRST for the engine)

- `test_money.py` — paise integrity; grep-test: no `float(` on amounts in `engine/`; no `openai` import in `engine/`.
- `test_matchers.py` — each rule: positive, negative, and boundary cases (±3-day window edges, fuzzy 0.84 vs 0.85, split payment two-partial-payments case → both unmatched not falsely merged, refund pair, duplicate 1-day apart vs 2-days apart).
- `test_reconciler_e2e.py` — seeded demo data → exactly the 4 expected exceptions, expected ledger totals (hardcode expected paise values).
- `test_migration_gst.py` — the §15 migration preserves page-1 data.
- `test_router_mock.py` — MOCK_MODE returns fixtures; failure path returns RouterError.
- `test_exports.py` — CSV row count; PDF generates non-empty.
- API smoke tests for every §8 endpoint using the demo store.

CI: GitHub Actions — pytest on every push (MOCK_MODE=true). Badge in README.

---

## 18. Build Order (9 days, submit Aug 2)

| Day | Deliverable (definition of done) |
|---|---|
| 1 (Jul 25) | Repo, AGENTS.md, Codex writes PLAN.md (committed), FastAPI+Next.js skeletons deployed to Render/Vercel ("hello" e2e), WS log streaming works, seed data files created |
| 2 | Intake: CSV parser (tested) + vision extraction for invoices & khaata (MOCK fixtures recorded) |
| 3 | **Engine day:** matchers + reconciler + full test suite green. Protect this day. |
| 4 | Exceptions workflow (agent + resolve API + cards UI) + Evidence Passport drawer |
| 5 | Risk radar + exports + demo-mode replay hardening |
| 6 | Voice note intake, Hindi Q&A + TTS, notice drafter, schema-drift path |
| 7 | Eval page + router cost chart, UI polish, i18n sweep, break-test demo mode 10× |
| 8 (Aug 1) | Record video, Google Doc, README, codex-log.md finalized |
| 9 (Aug 2) | Buffer, final deploy check on fresh browser + mobile, SUBMIT |

**Cut-line if behind schedule (drop in this order):** eval counterfactual chart → TTS (keep text answers) → notice drafter (keep risk radar) → schema-drift path. Never cut: demo mode, engine tests, Evidence Passport.

---

## 19. AGENTS.md content (copy to repo root)

```markdown
# AGENTS.md — Working agreement for Codex on PakkaHisaab

## Mission
Build per SPEC.md. You are the engineer; SPEC.md is the contract.

## Workflow (every task)
1. PLAN before code: for each milestone, write/update PLAN.md with steps and file list. Commit the plan separately.
2. TEST-FIRST for backend/engine: write pytest cases from SPEC §17 before implementation.
3. Run tests after every change. If red: read the traceback, fix, re-run. Log each fix cycle in docs/codex-log.md (one line: date, failure, fix).
4. SELF-REVIEW before ending a milestone: re-read your diff, list risks/smells in docs/codex-log.md, fix critical ones, then commit "milestone N: <name> (self-reviewed)".

## Hard rules
- All money = integer paise. Floats on amounts are bugs.
- engine/ and risk.py: no model calls, no openai imports, fully deterministic.
- model_router.py is the only OpenAI touchpoint. Every call logged to model_calls.
- Every external call: timeout + 1 retry + graceful fallback. Demo mode must survive total API failure.
- No secrets in code. Env vars only.
- Commit style: small, scoped, imperative ("add fuzzy party matcher + boundary tests"). Never squash away the plan/test/fix history — judges read it.

## Definition of done (project)
- Deployed URLs live, demo store loads with zero login, all 4 seeded exceptions reproduce,
  Evidence Passport opens for every ledger entry, exports download, CI green.
```

---

## 20. Submission Package Checklist

- [ ] Vercel URL (frontend) + Render URL (API) live, tested logged-out, tested on mobile
- [ ] Demo store: full flow < 2 min, zero login, survives airplane-mode API keys
- [ ] Public GitHub: README (problem, architecture diagram, model router table, Codex story, setup), CI badge green
- [ ] docs/codex-log.md shows plan → tests → fixes → self-review history
- [ ] 3-min video (script in project doc): hook (2026 GST-notice wave) → multimodal upload → agent terminal → exception + Evidence Passport → Hindi voice Q&A → schema-drift red-to-green → risk radar + notice reply → eval/cost chart → close
- [ ] Public Google Doc: theme, problem, solution, stack, architecture, Codex usage, screenshots
- [ ] Submitted on BlockseBlock by Aug 2 evening