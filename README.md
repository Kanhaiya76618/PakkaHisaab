# PakkaHisaab

**Five ways in, one truth out.**

A multimodal, multi-model AI agent that digitizes an Indian microbusiness's scattered
financial records — handwritten khaata photos, invoice images, UPI/bank CSVs, Hindi voice
notes — reconciles them into a verified cashbook where every number carries source
evidence, and protects the owner with GST notice-risk analysis.

Built for the ChatGPT Codex India Hackathon 2026 (BlockseBlock), theme #6 — AI for Bharat
Businesses.

---

## The core trust principle

> **AI reads and reasons; only code touches the math.**

Models extract and explain. Deterministic Python computes every total, match, and balance.
The AI never invents a financial fact — every number links to its source through an
Evidence Passport.

This is enforced, not just claimed:

- All money is **integer paise**. A test greps `backend/engine/` for `float(` and fails CI
  if it appears.
- `backend/engine/` — the reconciler, matchers, accounting identities, and risk scoring —
  imports no model client and makes no network call. A test greps for `openai` there too.
- `backend/model_router.py` is the **only** module that talks to a model provider. Every
  call writes a row to `model_calls`.

---

## Model router

`backend/model_router.py` is the single external-model touchpoint. Everything else calls
`route(task, payload)` or `route_with_fallback(task, payload)`.

| Task | Model | Provider | Why this model |
|---|---|---|---|
| `vision_khaata` | `gpt-4o` | OpenAI | Handwritten Devanagari + Latin numerals on a mixed-script ledger page |
| `vision_invoice` | `gpt-4o` | OpenAI | Structured but photographed documents |
| `vision_upi_screenshot` | `gpt-4o-mini` | OpenAI | Clean, simple structured screens — the large model is not needed |
| **`transcribe_indic`** | **`saaras:v3`** | **Sarvam AI** | **Indian sovereign AI model for code-mixed Indic speech, Whisper fallback.** `transcribe` mode normalizes spoken numbers to digits ("पच्चीस सौ" → 2500), which is what makes amount extraction from a Hindi voice note reliable |
| `transcribe_hi` | `whisper-1` | OpenAI | Fallback for `transcribe_indic` |
| `classify_txn` | `gpt-4o-mini` | OpenAI | Short classification: business/personal, entry type, party |
| `exception_reasoning` | `gpt-4o` | OpenAI | Explaining an anomaly in two languages |
| `notice_draft` | `gpt-4o` | OpenAI | Formal bilingual GST correspondence |
| `nl_query` | `gpt-4o-mini` | OpenAI | Phrasing an answer over figures that code has already computed |
| **`tts_indic`** | **`bulbul:v3`** | **Sarvam AI** | Hindi voice answers (`target_language_code: hi-IN`), OpenAI TTS fallback |
| `tts_hi` | `tts-1` | OpenAI | Fallback for `tts_indic` |

Every task gets a 30-second timeout and one retry. On final failure the router raises a
typed `RouterError` and callers degrade gracefully.

### Indic speech: Sarvam first, Whisper as the net

```
transcribe_indic (Sarvam saaras:v3)
      └── on RouterError ──▶ transcribe_hi (OpenAI whisper-1)

tts_indic (Sarvam bulbul:v3)
      └── on RouterError ──▶ tts_hi (OpenAI tts-1)
```

The fallback is explicit and **logged**: `model_calls` carries a `provider` column and a
`fallback_from` column, so the eval page reports which provider actually served a request
rather than which one we hoped would. The agent terminal says so too — if Sarvam is
unreachable, the log line names Whisper.

**Why Sarvam is primary for voice.** The seeded demo voice note says *"Ramesh ko pachchees
sau rupaye cash diye"*. Saaras v3 returns `रमेश को 2500 रुपये कैश दिए` — the amount as
digits. Whisper returns `रमेश को पच्चीस सौ रुपये कैश दिए`, with the number spelled out.
Our amount extractor reads digits only and returns nothing rather than guessing, so the
provider choice is the difference between ₹2,500 landing in the ledger and no amount at
all. The eval page shows this side by side as **"Indic ASR: Sarvam vs Whisper"**.

**Cost, in the currency each vendor bills.** Sarvam prices speech-to-text at **₹30/hour**;
OpenAI prices tokens in USD. `model_calls` stores `cost_inr` and `cost_usd` separately with
a `currency` label, and the eval page shows both. Collapsing them into one number would
require an FX rate we do not have — an invented figure inside a financial product.

---

## What it does

**1 · Digitize** — multimodal intake. CSVs are parsed by pure Python (no model, confidence
1.0). Khaata and invoice photos go to vision extraction. Hindi voice notes go to Sarvam.
Every extracted row keeps a reference back to where it came from.

**2 · Reconcile** — a deterministic engine normalizes parties (Devanagari → Latin,
honorifics stripped), then applies five matching rules in strict priority: `exact_ref`,
`exact_amount_date`, `amount_within_window` (±3 days), `fuzzy_party_amount` (token-set
≥ 0.85), `voice_confirmed`. Anything below 0.8 becomes an exception. Four anomaly detectors
run in pure code: unmatched invoice, possible duplicate, khaata arithmetic error, and
personal-vs-business.

**3 · Protect** — `engine/risk.py` scores GST notice risk deterministically:
`gap 60% + open exceptions 25% + personal/business ambiguity 15%`, all integer paise and
rounded integer percentages. The UI shows the component breakdown, not just the number.

**The Evidence Passport** — click any ledger row and see every source that supports it:
filename, where inside the file, what the extractor read versus what the ledger holds,
its confidence, which model produced it, and why the match was made in plain language
("Matched because the amount and date are identical") in Hindi and English.

---

## Running it

```bash
git clone <repo> && cd PakkaHisaab
```

Backend:

```bash
cd backend && python3.11 -m venv .venv && .venv/bin/pip install -e '.[dev]'
```

```bash
cd backend && MOCK_MODE=true .venv/bin/uvicorn main:app --port 8000
```

Frontend:

```bash
cd frontend && npm install && npm run dev
```

Then open <http://localhost:3000> and click **Open demo store**. No login.

Tests — the whole suite runs keyless:

```bash
cd backend && MOCK_MODE=true .venv/bin/pytest tests
```

### `MOCK_MODE` and honest fixtures

`MOCK_MODE=true` makes the router return canned fixtures from `sample_data/fixtures/`
instead of calling a provider. This is what lets the test suite run without any API key and
what keeps the demo alive if every external API fails.

Fixtures state their own provenance. The vision and speech fixtures currently in the
repository are labelled **PLACEHOLDER**: they match each provider's documented response
schema and are ground-truthed against `sample_data/GROUND_TRUTH.md`, but they were not
captured from a live call, because no usable `OPENAI_API_KEY` or `SARVAM_API_KEY` was
available while they were written. Read `sample_data/fixtures/*.json` — each one says so in
its `_provenance` field. Replace them by recording once against real keys and diffing every
field against the ground truth.

### Environment

Every variable is documented in `.env.example`; none are committed. `SARVAM_API_KEY` is
optional — without it, Indic tasks fall back to OpenAI and the fallback is recorded.
Deployment steps for Railway (backend) and Vercel (frontend) are in `DEPLOY.md`.

---

## Architecture

```
Next.js 14 (Vercel)                FastAPI (Railway)              Supabase
├── /store/[id]/digitize           ├── model_router.py ──────▶ OpenAI + Sarvam AI
├── /store/[id]/hisaab   ◀──WS──▶  ├── agents/  (orchestration)
├── /store/[id]/kavach             ├── engine/  (NO models, all paise)
├── /store/[id]/evals              │   ├── reconciler.py + matchers.py
└── /codex-log                     │   ├── accounting.py
                                   │   └── risk.py
                                   ├── evidence.py  (Evidence Passport)
                                   └── exports.py   (CSV + PDF pack)
```

**Authorization is doubled deliberately.** The backend uses the Supabase service-role key —
it must, because background agents write on behalf of the user — and that key *bypasses*
RLS. So `authorize_store` in `backend/auth.py` is the real gate for API traffic, and the
row-level-security policies in `supabase/migrations/` are the safety net for any direct
browser-to-Supabase query. The public demo store is expressed as an RLS policy
(`is_public`), not a special case in code.

---

## How this was built

`docs/codex-log.md` is the running build log: plan → tests-first → every failure and its
diagnosis → self-review, written as the work happened. It is also rendered in the app at
`/codex-log`.

The project was started by **Codex** and continued by **Claude Code** after Codex ran out
of credits. The handover is logged as a verified-by-execution audit — every subsystem rated
against what actually ran, not against what the plan claimed — under
*"Agent handover: Codex → Claude Code"*. Entries are attributed to whichever agent wrote
them; nothing was backfilled or reattributed.

`AGENTS.md` is the working agreement both agents follow. `SPEC.md` and
`SPEC_PATCH_SUPABASE.md` are the product contract (the patch wins on conflict);
`DESIGN.md` is the frontend contract.
