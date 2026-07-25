-- Preserve UPI reference evidence for deterministic exact-reference matching.
alter table public.extracted_entries
  add column if not exists upi_ref text;

create index if not exists extracted_entries_upi_ref_idx
  on public.extracted_entries (upi_ref)
  where upi_ref is not null;
