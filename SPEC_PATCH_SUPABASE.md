# SPEC PATCH — Supabase Auth, Multi-Tenancy & Storage

> **Instruction to Codex:** This patch amends `SPEC.md`. Where it conflicts with the original spec, **this patch wins**. Append it as `SPEC.md` §21–§29 (or paste inline). Re-read §17 test requirements — this patch adds mandatory authorization tests.

---

## 21. What Supabase Replaces

| Original spec | Now |
|---|---|
| SQLite file DB | **Supabase Postgres** |
| No auth | **Supabase Auth** (Google OAuth + magic link) |
| Local `sample_data/` file serving | **Supabase Storage** (two buckets) |
| Alembic migrations | **Supabase migrations** (`supabase/migrations/*.sql`) via CLI — keep the §15 schema-drift demo, just executed as a real SQL migration through the CLI instead of Alembic |
| — | **RLS policies** as defense-in-depth (new) |

Unchanged: FastAPI backend, Next.js frontend, the deterministic engine, the model router, agent architecture, Evidence Passport, everything in §6–§16.

**Keep FastAPI WebSockets for the agent terminal.** Supabase Realtime could do this, but it's rework with no judging upside. Do not switch.

---

## 22. Project Setup & Environment

```bash
npm i -g supabase
supabase init
supabase link --project-ref <ref>
supabase db push          # applies supabase/migrations/*
```

**Env vars (never commit; `.env.example` documents them):**

```bash
# frontend (Vercel)
NEXT_PUBLIC_SUPABASE_URL=https://<ref>.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=...          # safe to expose; RLS protects data
NEXT_PUBLIC_API_URL=https://<render-app>.onrender.com

# backend (Render)
SUPABASE_URL=https://<ref>.supabase.co
SUPABASE_SERVICE_ROLE_KEY=...              # SERVER ONLY. Never in frontend, never in a NEXT_PUBLIC_ var.
SUPABASE_JWT_SECRET=...                    # for verifying user tokens
DATABASE_URL=postgresql://postgres.<ref>:<pw>@aws-0-<region>.pooler.supabase.com:5432/postgres
OPENAI_API_KEY=...
MOCK_MODE=false
DEMO_STORE_ID=00000000-0000-0000-0000-000000000001
```

**Two gotchas that will cost you an evening if missed:**

1. **Use the pooler connection string (`...pooler.supabase.com`), not the direct `db.<ref>.supabase.co` host.** Direct connections are IPv6-only and Render's free tier is IPv4 — you'll get inexplicable connection timeouts. Use session mode (port 5432) for the persistent FastAPI process.
2. **Free-tier projects pause after ~7 days of inactivity.** Your deadline is inside that window, but judges may open the app days after submission. Add an uptime pinger (cron-job.org, free) hitting `GET /api/health` every 10 minutes from Aug 1 onward, and mention it in the README.

---

## 23. Schema Changes (Postgres)

Convert all `TEXT PK` ids to `uuid PRIMARY KEY DEFAULT gen_random_uuid()`, all timestamps to `timestamptz DEFAULT now()`, all `TEXT CHECK(...)` enums to real Postgres enums, and JSON columns to `jsonb`.

**New / changed tables:**

```sql
-- Supabase Auth owns auth.users. Mirror the bits we need:
create table public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  display_name text,
  preferred_lang text not null default 'hi' check (preferred_lang in ('hi','en')),
  created_at timestamptz not null default now()
);

-- auto-create profile on signup
create function public.handle_new_user() returns trigger
language plpgsql security definer set search_path = '' as $$
begin
  insert into public.profiles (id, display_name)
  values (new.id, coalesce(new.raw_user_meta_data->>'full_name', new.email));
  return new;
end; $$;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- stores: add ownership + demo flags
alter table public.stores
  add column owner_user_id uuid references auth.users(id) on delete cascade,
  add column is_public boolean not null default false,
  add column is_demo   boolean not null default false;

-- exactly one public demo store
create unique index one_public_demo on public.stores (is_public) where is_public;
```

Every child table (`source_documents`, `extracted_entries`, `ledger_entries`, `matches`, `exceptions`, `gst_notices`) must carry a `store_id uuid not null references public.stores(id) on delete cascade` — including tables that previously reached the store indirectly. RLS policies need a direct path, and cascading deletes make account deletion trivial.

`model_calls` stays global (no store_id) — it's operational telemetry for the eval page.

---

## 24. Row Level Security (write these policies; they are also your authorization tests' target)

Enable RLS on **every** public table. The demo store is expressed as a policy, not a special case in code.

```sql
alter table public.stores enable row level security;

-- read: your own stores, or the public demo
create policy stores_select on public.stores for select
  using (is_public or owner_user_id = auth.uid());

-- write: only your own
create policy stores_insert on public.stores for insert
  with check (owner_user_id = auth.uid());
create policy stores_update on public.stores for update
  using (owner_user_id = auth.uid());
create policy stores_delete on public.stores for delete
  using (owner_user_id = auth.uid());
```

Reusable helper for child tables:

```sql
create function public.can_read_store(sid uuid) returns boolean
language sql stable security definer set search_path = public as $$
  select exists (
    select 1 from public.stores s
    where s.id = sid and (s.is_public or s.owner_user_id = auth.uid())
  );
$$;

create function public.can_write_store(sid uuid) returns boolean
language sql stable security definer set search_path = public as $$
  select exists (
    select 1 from public.stores s
    where s.id = sid and (s.owner_user_id = auth.uid() or s.is_demo)
  );
$$;
```

Then for each child table (repeat verbatim, substituting the table name):

```sql
alter table public.ledger_entries enable row level security;
create policy le_select on public.ledger_entries for select using (can_read_store(store_id));
create policy le_write  on public.ledger_entries for all    using (can_write_store(store_id))
                                                            with check (can_write_store(store_id));
```

Note `can_write_store` allows writes to the demo store by anyone — deliberate, because judges must be able to resolve an exception and watch it work. The nightly/half-hourly reset (§27) contains the blast radius.

---

## 25. Auth Flow

**Providers:** Google OAuth (primary — one tap on mobile, which is what a shopkeeper uses) and magic-link email (fallback). **No password auth** — less code, less attack surface, better UX.

**Frontend:** `@supabase/ssr` with the Next.js App Router. Create `lib/supabase/client.ts` (browser), `lib/supabase/server.ts` (server components), and `middleware.ts` for session refresh. Follow the current `@supabase/ssr` cookie pattern — do **not** use the deprecated `@supabase/auth-helpers-nextjs`.

**Route protection:**
- `/` and `/store/<DEMO_STORE_ID>/*` — public, no session required.
- `/store/<other-id>/*` and `/dashboard` — redirect to `/login` if no session.

**Backend JWT verification** — one FastAPI dependency, used by every store-scoped route:

```python
# backend/auth.py
from fastapi import Depends, HTTPException, Header
import jwt

async def current_user(authorization: str | None = Header(None)) -> str | None:
    """Returns user_id, or None for anonymous callers (demo store access)."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    try:
        payload = jwt.decode(
            authorization[7:], SUPABASE_JWT_SECRET,
            algorithms=["HS256"], audience="authenticated",
        )
        return payload["sub"]
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid token")

async def authorize_store(store_id: str, user_id: str | None = Depends(current_user)):
    store = await db.get_store(store_id)          # service-role read
    if not store:
        raise HTTPException(404, "Store not found")
    if store.is_public or (user_id and store.owner_user_id == user_id):
        return store
    raise HTTPException(403, "Not your store")
```

**Why both RLS and FastAPI checks?** The backend uses the service role key (it must — it writes agent output on behalf of background tasks), which *bypasses* RLS. So `authorize_store` is the real gate for API traffic, and RLS is the safety net for any direct frontend-to-Supabase query. Say this explicitly in the README architecture section; it reads as security maturity to a technical judge.

---

## 26. Storage

Two buckets:

| Bucket | Public? | Contents |
|---|---|---|
| `demo-assets` | public | seeded khaata photos, invoices, CSVs, audio — judges load these with no auth |
| `user-uploads` | private | real users' documents; served via signed URLs (1-hour expiry) |

Path convention: `{bucket}/{store_id}/{document_id}.{ext}` — this makes the storage RLS policy a simple path prefix check against store ownership.

```sql
create policy user_uploads_rw on storage.objects for all
  using (bucket_id = 'user-uploads' and can_read_store((storage.foldername(name))[1]::uuid))
  with check (bucket_id = 'user-uploads' and can_write_store((storage.foldername(name))[1]::uuid));
```

The Evidence Passport thumbnail URLs (§9) must be signed URLs for private stores and plain public URLs for the demo store — one helper function, `get_document_url(doc)`, handles both.

---

## 27. Demo Store Reset Job (do not skip this)

Without it, judge #3 opens the app and finds every exception already resolved by judge #1 — your demo looks broken.

**Implementation:** a `pg_cron` job (Supabase supports it) calling a Postgres function every 30 minutes:

```sql
create function public.reset_demo_store() returns void
language plpgsql security definer set search_path = public as $$
begin
  delete from public.ledger_entries where store_id = '<DEMO_STORE_ID>';
  delete from public.exceptions    where store_id = '<DEMO_STORE_ID>';
  delete from public.matches       where ledger_entry_id not in (select id from public.ledger_entries);
  -- re-insert from the immutable snapshot tables
  insert into public.ledger_entries select * from demo_snapshot.ledger_entries;
  insert into public.exceptions     select * from demo_snapshot.exceptions;
end; $$;

select cron.schedule('reset-demo', '*/30 * * * *', 'select public.reset_demo_store()');
```

Keep a `demo_snapshot` schema holding the pristine seed rows — `source_documents` and `extracted_entries` are never mutated by the UI, so they don't need resetting.

Also add a manual **"Reset demo data"** button in the demo store's header, calling `POST /api/demo/reset`. Use it right before you record the video, and mention it in the Google Doc so judges can self-serve a clean state.

---

## 28. Onboarding for Real Users

After first sign-in: create an empty store named from their profile, then show a two-option card — **"Load sample data"** (clones the demo fixtures into their store, so they immediately see the product work) or **"Upload my records"** (straight to the Digitize tab). Never show a new user an empty dashboard.

---

## 29. Added Test Requirements (append to §17)

These are the tests a technically sharp judge would try by hand, so they must exist:

- `test_authz_api.py` — for **every** store-scoped endpoint in §8:
  - anonymous → demo store: **200**
  - anonymous → private store: **403**
  - user A's token → user B's store: **403**
  - user A's token → user A's store: **200**
  - malformed/expired JWT: **401**
- `test_rls.py` — using the **anon key** (not service role), attempt a direct `select` on another user's `ledger_entries` and assert zero rows; attempt an `insert` into another user's store and assert failure.
- `test_storage_paths.py` — signed URL for a private doc works; the same object's public URL 404s.
- `test_demo_reset.py` — mutate the demo store, run `reset_demo_store()`, assert the 4 seeded exceptions are back and `status='open'`.
- `test_cascade_delete.py` — deleting a user removes their stores and all child rows.

CI runs these against a local `supabase start` instance with `MOCK_MODE=true`.

---

## 30. Build Order Deltas

| Day | Added work |
|---|---|
| 1 | Supabase project, `supabase init`, initial migration, RLS policies, Google OAuth configured, `@supabase/ssr` wired, `authorize_store` dependency, demo store row seeded |
| 2 | Storage buckets + upload path convention + signed-URL helper |
| 5 | Demo reset job (pg_cron + manual button) + onboarding cards |
| 7 | Authorization test sweep (§29) — budget 2 hours; this is where cross-tenant bugs surface |

Net cost ≈ 1 day, absorbed inside the existing 9-day plan. **The cut-line does not move.** If you fall behind, the thing you cut is still the eval counterfactual chart — never auth tests, never the demo reset.

---

## 31. One Line for the Video and Google Doc

> "The live demo requires no login — one click opens a fully seeded store. Accounts exist for real merchants who need private, persistent data, protected by Postgres row-level security."

State it explicitly. It preempts any doubt about the viability gate and turns your auth work from a rule risk into a credibility point.