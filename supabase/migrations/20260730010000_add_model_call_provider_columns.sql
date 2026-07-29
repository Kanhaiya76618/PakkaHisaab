-- Sarvam AI joins OpenAI in the model router, so `model_calls` must record *which*
-- provider served a request and in which currency it was billed.
--
-- Costs are kept in two columns rather than converted into one: Sarvam prices speech in
-- INR (₹30/hour) and OpenAI prices tokens in USD. Collapsing them would require an FX
-- rate we do not have, which would put an invented number in a financial product. The
-- eval page reads `currency` and labels each figure instead.

alter table public.model_calls
  add column if not exists provider text not null default 'openai'
    check (provider in ('openai', 'sarvam')),
  add column if not exists cost_inr real not null default 0,
  add column if not exists currency text not null default 'USD'
    check (currency in ('USD', 'INR')),
  -- Set when this call is a fallback: names the task whose primary provider failed.
  add column if not exists fallback_from text;

comment on column public.model_calls.provider is
  'Which vendor actually served the call — the fallback chain means it is not inferable from task.';
comment on column public.model_calls.fallback_from is
  'Non-null when this call served as a fallback, naming the task that failed first.';

create index if not exists model_calls_provider_idx on public.model_calls (provider);
