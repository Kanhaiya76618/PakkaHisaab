# Udhaar Book

A lightweight credit‑ledger web app for small shop owners.

## Features
- Add customers and credit/repayment entries (persisted in `localStorage`).
- "Who owes me" page shows amount, age, and on‑time/overdue status.
- Draft bilingual reminders with deterministic tone selection.
- Cash‑flow view with receivables, weekly collections, and trend chart.
- No login, no API keys required for the demo.
- Optional OpenAI‑API‑based wording when `OPENAI_API_KEY` is set.

## Stack
- **Next.js 14** (App Router)
- **TypeScript**
- **Tailwind CSS** (dark‑mode, mobile‑first)
- **Vitest** for unit tests
- **Playwright** for a smoke test

## Development
```bash
npm install
npm run dev   # http://localhost:3000
```

## Tests
```bash
npm test               # Vitest unit tests
npx playwright test    # Smoke test
```

## Build & Deploy
```bash
npm run build   # generates .next
# Deploy the `/.next` folder on Vercel (no env vars needed).
```

## Environment
Copy `.env.example` to `.env` and optionally add `OPENAI_API_KEY` to enable LLM‑based reminder generation.
