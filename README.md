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

OpenAI-family tasks reach the vendor one of two ways, decided at call time: **Azure OpenAI**
when `AZURE_OPENAI_*` is configured, otherwise a direct `OPENAI_API_KEY`. Azure routes by
*deployment name* rather than model id and requires `max_completion_tokens`, so
`model_calls` records the deployment that actually served the call, not the model id we
asked for. Azure serves `chat`-modality tasks only — a text deployment cannot transcribe
audio, and the router refuses to send it any.

| Task | Model | Provider | Why this model |
|---|---|---|---|
| `vision_khaata` | `gpt-4o` | OpenAI | Handwritten Devanagari + Latin numerals on a mixed-script ledger page |
| `vision_invoice` | `gpt-4o` | OpenAI | Structured but photographed documents |
| `vision_upi_screenshot` | `gpt-4o-mini` | OpenAI | Clean, simple structured screens — the large model is not needed |
| **`transcribe_indic`** | **`saaras:v3`** | **Sarvam AI** | **Indian sovereign AI model for code-mixed Indic speech, Whisper fallback.** Verified live on real audio; usually normalizes spoken amounts to digits, but see the measured caveat below |
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

**Why Sarvam is primary for voice — and what was actually measured.** The seeded voice note
says *"Ramesh ko pachchees sau rupaye cash diye"*. `sample_data/voice_ramesh.wav` is real
audio, synthesized by Sarvam Bulbul v3 and committed, and Saaras v3 transcribes it as
`रमेश को ₹2500 कैश दिए, याद रखना।` — the amount as digits, **identically on 5 of 5
consecutive live calls**.

That normalization is **not a guarantee**, and pretending otherwise would be the kind of
claim this project exists to avoid. The same sentence, synthesized with different prosody,
came back as `रमेश को पच्चीस सौ रुपये कैश दिए` with the number in words. Both outcomes were
measured, not assumed.

So the amount extractor does not depend on it. Digits are read first; when a transcript has
none, `engine/indic_numbers.py` parses the Hindi/Hinglish number words in deterministic code
— `पच्चीस सौ` → 2500, `चार हज़ार आठ सौ` → 4800, `ढाई हज़ार` → 2500, all integer arithmetic.
The eval page shows both paths under **"Indic ASR: measured on real audio"**.

Whisper is honestly reported as **not measured**: there is no `OPENAI_API_KEY` and the Azure
resource has no `whisper` deployment, so the head-to-head has not been run. It is excluded
from the category score rather than given a fabricated result — an unrun test is not a
failure, and it is certainly not a pass.

**Cost, in the currency each vendor bills.** Sarvam prices speech-to-text at **₹30/hour**;
OpenAI prices tokens in USD. `model_calls` stores `cost_inr` and `cost_usd` separately with
a `currency` label, and the eval page shows both. Collapsing them into one number would
require an FX rate we do not have — an invented figure inside a financial product.

Two flags keep that telemetry honest rather than merely present:

- `from_fixture` — a committed fixture answered, so no vendor saw the call. `provider` still
  names the vendor that owns the task, so currency and the provider breakdown stay right.
- `cost_known` — false when no published price exists for the model. A custom Azure
  deployment on a per-agreement rate records its **real token counts** with the money marked
  unknown. Reporting `$0.00` for a call that cost money would be a fabricated number.

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

The demo's headline exception is backed by a **real document**: `sample_data/mehta_inv_231.jpg`
is a photograph of a printed ₹4,800 invoice (INV-231, 12/07/2026) with no matching UPI
payment anywhere in the July export — so the engine derives an `unmatched_invoice`, and the
Evidence Passport cites the actual photographed bill. `sample_data/generate.py` refuses to
overwrite it, and a test enforces that.

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

Fixtures state their own provenance, and they are not all equally strong:

- `vision_invoice.json` is a **LIVE RECORDING**, not a placeholder. It was captured by
  routing `vision_invoice` through the real router against `mehta_inv_231.jpg` — a photograph
  of an actual printed invoice — and it holds the model's verbatim output. Every field ground
  truth can adjudicate came back correct: ₹4,800, 2026-07-12, `purchase`, invoice 231, and
  all three line items with their rates and extensions. Re-record any time with
  `python scripts/record_vision_fixture.py --task vision_invoice --image sample_data/mehta_inv_231.jpg`.
- `vision_khaata.json` is a **PLACEHOLDER against a generated image**. It proves the
  pipeline's shape, not real handwriting OCR. Photographing a real khaata page is the
  highest-value fixture upgrade left.
- `transcribe_indic.json` and `tts_indic.json` are **LIVE RECORDINGS** from Sarvam.
  `tts_indic.json` carries real synthesized Hindi speech (~210 KB of WAV as base64), not
  placeholder silence, and `sample_data/voice_ramesh.wav` is the committed audio asset SPEC
  §11 asks for — generated by Bulbul v3, so it is synthetic speech rather than a human
  recording, and labelled as such.
- `transcribe_hi.json`, `tts_hi.json`, and `classify_txn.json` are still **PLACEHOLDER**.
  Whisper and OpenAI TTS have no route from here at all: no `OPENAI_API_KEY`, and the Azure
  resource has no audio deployments. The router refuses to send audio to a text deployment
  rather than doing something that looks like it worked.

Every file says which of these it is in its own `_provenance` field, and
`sample_data/fixtures/README.md` explains the difference. Nothing in this repository claims
a live model call that did not happen.

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
