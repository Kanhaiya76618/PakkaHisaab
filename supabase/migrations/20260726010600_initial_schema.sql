-- PakkaHisaab initial schema. Apply with: supabase db push
create extension if not exists pgcrypto;

create type public.store_language as enum ('hi', 'en');
create type public.document_kind as enum (
  'khaata_photo', 'invoice_image', 'invoice_pdf', 'bank_csv', 'upi_csv',
  'upi_screenshot', 'voice_note', 'manual', 'gst_notice'
);
create type public.document_status as enum ('pending', 'processing', 'processed', 'failed');
create type public.entry_type as enum (
  'sale', 'purchase', 'payment_in', 'payment_out', 'credit_given',
  'credit_received', 'note'
);
create type public.ledger_status as enum ('verified', 'pending_confirmation');
create type public.ledger_created_by as enum ('reconciler', 'user');
create type public.exception_kind as enum (
  'unmatched_invoice', 'unmatched_payment', 'possible_duplicate', 'amount_mismatch',
  'personal_vs_business', 'arithmetic_error'
);
create type public.exception_status as enum ('open', 'resolved', 'dismissed');

create table public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  full_name text,
  avatar_url text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.stores (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  owner_name text,
  lang public.store_language not null default 'hi',
  owner_user_id uuid references auth.users(id) on delete cascade,
  is_public boolean not null default false,
  is_demo boolean not null default false,
  created_at timestamptz not null default now()
);
create unique index one_public_demo on public.stores (is_public) where is_public;

create table public.source_documents (
  id uuid primary key default gen_random_uuid(),
  store_id uuid not null references public.stores(id) on delete cascade,
  kind public.document_kind not null,
  filename text not null,
  storage_bucket text not null default 'user-uploads',
  storage_path text,
  page_no integer,
  raw_text text,
  uploaded_at timestamptz not null default now(),
  processed_at timestamptz,
  status public.document_status not null default 'pending'
);

create table public.extracted_entries (
  id uuid primary key default gen_random_uuid(),
  store_id uuid not null references public.stores(id) on delete cascade,
  source_document_id uuid not null references public.source_documents(id) on delete cascade,
  entry_type public.entry_type not null,
  party_name text,
  amount_paise integer not null,
  currency text not null default 'INR',
  entry_date date,
  description text not null default '',
  confidence real not null check (confidence between 0 and 1),
  extraction_model text,
  bbox_or_line_ref text,
  created_at timestamptz not null default now()
);

create table public.ledger_entries (
  id uuid primary key default gen_random_uuid(),
  store_id uuid not null references public.stores(id) on delete cascade,
  entry_type public.entry_type not null,
  party_name text,
  amount_paise integer not null,
  entry_date date not null,
  description text not null default '',
  status public.ledger_status not null default 'pending_confirmation',
  created_by public.ledger_created_by not null,
  created_at timestamptz not null default now()
);

create table public.matches (
  id uuid primary key default gen_random_uuid(),
  store_id uuid not null references public.stores(id) on delete cascade,
  ledger_entry_id uuid not null references public.ledger_entries(id) on delete cascade,
  extracted_entry_id uuid not null references public.extracted_entries(id) on delete cascade,
  match_rule text not null,
  match_score real not null check (match_score between 0 and 1),
  created_at timestamptz not null default now()
);

create table public.exceptions (
  id uuid primary key default gen_random_uuid(),
  store_id uuid not null references public.stores(id) on delete cascade,
  kind public.exception_kind not null,
  summary_en text not null,
  summary_hi text not null,
  related_extracted_ids jsonb not null default '[]'::jsonb,
  suggested_action jsonb not null default '{}'::jsonb,
  status public.exception_status not null default 'open',
  resolved_at timestamptz,
  resolution text,
  created_at timestamptz not null default now()
);

create table public.model_calls (
  id uuid primary key default gen_random_uuid(),
  task text not null,
  model text not null,
  input_tokens integer not null default 0,
  output_tokens integer not null default 0,
  cost_usd real not null default 0,
  latency_ms integer not null default 0,
  success boolean not null,
  created_at timestamptz not null default now()
);

create table public.gst_notices (
  id uuid primary key default gen_random_uuid(),
  store_id uuid not null references public.stores(id) on delete cascade,
  source_document_id uuid references public.source_documents(id) on delete set null,
  raw_text text not null,
  flagged_items jsonb not null default '[]'::jsonb,
  draft_reply text,
  created_at timestamptz not null default now()
);

create index source_documents_store_id_idx on public.source_documents(store_id);
create index extracted_entries_store_id_idx on public.extracted_entries(store_id);
create index ledger_entries_store_id_idx on public.ledger_entries(store_id);
create index matches_store_id_idx on public.matches(store_id);
create index exceptions_store_id_idx on public.exceptions(store_id);
create index gst_notices_store_id_idx on public.gst_notices(store_id);

create or replace function public.handle_new_user()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  insert into public.profiles (id, full_name, avatar_url)
  values (new.id, new.raw_user_meta_data ->> 'full_name', new.raw_user_meta_data ->> 'avatar_url')
  on conflict (id) do nothing;
  return new;
end;
$$;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

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

alter table public.profiles enable row level security;
create policy profiles_select_own on public.profiles for select using (id = auth.uid());
create policy profiles_update_own on public.profiles for update using (id = auth.uid()) with check (id = auth.uid());

alter table public.stores enable row level security;
create policy stores_select on public.stores for select using (is_public or owner_user_id = auth.uid());
create policy stores_insert on public.stores for insert with check (owner_user_id = auth.uid());
create policy stores_update on public.stores for update using (owner_user_id = auth.uid()) with check (owner_user_id = auth.uid());
create policy stores_delete on public.stores for delete using (owner_user_id = auth.uid());

alter table public.source_documents enable row level security;
create policy source_documents_select on public.source_documents for select using (public.can_read_store(store_id));
create policy source_documents_write on public.source_documents for all using (public.can_write_store(store_id)) with check (public.can_write_store(store_id));
alter table public.extracted_entries enable row level security;
create policy extracted_entries_select on public.extracted_entries for select using (public.can_read_store(store_id));
create policy extracted_entries_write on public.extracted_entries for all using (public.can_write_store(store_id)) with check (public.can_write_store(store_id));
alter table public.ledger_entries enable row level security;
create policy ledger_entries_select on public.ledger_entries for select using (public.can_read_store(store_id));
create policy ledger_entries_write on public.ledger_entries for all using (public.can_write_store(store_id)) with check (public.can_write_store(store_id));
alter table public.matches enable row level security;
create policy matches_select on public.matches for select using (public.can_read_store(store_id));
create policy matches_write on public.matches for all using (public.can_write_store(store_id)) with check (public.can_write_store(store_id));
alter table public.exceptions enable row level security;
create policy exceptions_select on public.exceptions for select using (public.can_read_store(store_id));
create policy exceptions_write on public.exceptions for all using (public.can_write_store(store_id)) with check (public.can_write_store(store_id));
alter table public.gst_notices enable row level security;
create policy gst_notices_select on public.gst_notices for select using (public.can_read_store(store_id));
create policy gst_notices_write on public.gst_notices for all using (public.can_write_store(store_id)) with check (public.can_write_store(store_id));
alter table public.model_calls enable row level security;
-- model_calls has no browser policy: evaluation telemetry is served by the backend service role.

insert into storage.buckets (id, name, public)
values ('demo-assets', 'demo-assets', true), ('user-uploads', 'user-uploads', false)
on conflict (id) do update set public = excluded.public;

create policy user_uploads_select on storage.objects for select
using (bucket_id = 'user-uploads' and name ~ '^[0-9a-f-]{36}/' and public.can_read_store(split_part(name, '/', 1)::uuid));
create policy user_uploads_write on storage.objects for all
using (bucket_id = 'user-uploads' and name ~ '^[0-9a-f-]{36}/' and public.can_write_store(split_part(name, '/', 1)::uuid))
with check (bucket_id = 'user-uploads' and name ~ '^[0-9a-f-]{36}/' and public.can_write_store(split_part(name, '/', 1)::uuid));

insert into public.stores (id, name, owner_name, lang, is_public, is_demo)
values ('00000000-0000-0000-0000-000000000001', 'Sharma Kirana Demo', 'Sharma Kirana', 'hi', true, true);
