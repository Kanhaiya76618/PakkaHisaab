# PakkaHisaab frontend milestone

## Goal

Build the responsive, bilingual Next.js frontend for the authenticated PakkaHisaab
experience before connecting the FastAPI backend.

## Scope

1. Scaffold a strict TypeScript Next.js 14 + Tailwind application in `frontend/`.
2. Establish the supplied semantic light/dark token system and bilingual typography.
3. Build the login, landing, Digitize, Hisaab, Kavach, Evals, and Codex Log surfaces
   with realistic typed demo data and their loading, empty, error, and success states.
4. Implement accessible interaction primitives: theme/language controls, navigation,
   upload affordance, agent terminal, evidence drawer, exceptions, and charts.
5. Verify production build and inspect the rendered application at desktop and mobile
   widths before API wiring begins.

## Deferred to backend integration

- Real authentication and authorization.
- Persistent uploads, WebSocket streaming, reconciliation, exports, and AI calls.
- Data fetching with SWR and Zod endpoint validation.
