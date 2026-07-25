-- Align the already-applied initial profile table with SPEC_PATCH_SUPABASE §23.
alter table public.profiles
  add column if not exists display_name text,
  add column if not exists preferred_lang text not null default 'hi'
    check (preferred_lang in ('hi', 'en'));

update public.profiles
set display_name = coalesce(display_name, full_name)
where display_name is null;

alter table public.profiles
  drop column if exists avatar_url,
  drop column if exists full_name,
  drop column if exists updated_at;

create or replace function public.handle_new_user()
returns trigger language plpgsql security definer set search_path = '' as $$
begin
  insert into public.profiles (id, display_name)
  values (new.id, coalesce(new.raw_user_meta_data ->> 'full_name', new.email));
  return new;
end;
$$;
