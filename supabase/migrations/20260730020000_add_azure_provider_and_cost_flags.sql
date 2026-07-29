-- Azure OpenAI joins the router as a third provider, and two honesty flags join
-- `model_calls` alongside it.
--
-- `from_fixture` — MOCK_MODE served a committed fixture, so no vendor saw this call.
--   `provider` still names the vendor that owns the task, which is what keeps cost currency
--   and the eval page's provider breakdown correct; this flag stops the row from implying a
--   request that never left the process.
--
-- `cost_known` — false when no published price exists for `model`. Azure deployments carry
--   arbitrary names on per-agreement rates, so a real call against an unpriced deployment
--   records its true token counts with the money marked unknown. Reporting $0.00 for a call
--   that cost money would be a fabricated figure.

alter table public.model_calls
  drop constraint if exists model_calls_provider_check;

alter table public.model_calls
  add constraint model_calls_provider_check
    check (provider in ('openai', 'azure_openai', 'sarvam'));

alter table public.model_calls
  add column if not exists from_fixture boolean not null default false,
  add column if not exists cost_known   boolean not null default true;

comment on column public.model_calls.from_fixture is
  'True when a committed fixture answered instead of the vendor (MOCK_MODE).';
comment on column public.model_calls.cost_known is
  'False when no published price exists for `model`; token counts are still real.';

create index if not exists model_calls_from_fixture_idx on public.model_calls (from_fixture);
