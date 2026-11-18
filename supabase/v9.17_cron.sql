-- v9.17 — configuration et planification des rappels (déjà appliquées sur le projet de production).
-- Les valeurs secrètes (clé privée VAPID, clé du planificateur) sont déposées dans public.ptua_push_cfg et ne figurent pas ici.
create table if not exists public.ptua_push_cfg (k text primary key, v text not null);
alter table public.ptua_push_cfg enable row level security;
revoke all on public.ptua_push_cfg from anon, authenticated;
-- insert into public.ptua_push_cfg(k,v) values ('vapid_public','…'),('vapid_private','…'),('cron_key','…');
create extension if not exists pg_net with schema extensions;
create extension if not exists pg_cron with schema pg_catalog;
create or replace function public.ptua_push_tick() returns void language sql security definer set search_path = '' as $$
  select net.http_post(url:='https://iofbwpzhptctyelmylkz.supabase.co/functions/v1/ptua-push',
    headers:=jsonb_build_object('x-cron-key',(select v from public.ptua_push_cfg where k='cron_key')));
$$;
revoke all on function public.ptua_push_tick() from public, anon, authenticated;
select cron.schedule('ptua-push-tick','*/10 * * * *','select public.ptua_push_tick()');
