-- v9.17 — Rappels sur le téléphone (Web Push). À appliquer UNE fois sur le projet Supabase de PTUA.
-- N'ajoute qu'une table et deux fonctions ; ne modifie rien d'existant. Aucune donnée de marché n'y est stockée : uniquement
-- l'adresse de notification du téléphone et des instants d'alerte (dates), rattachés à l'identifiant de synchronisation.
create table if not exists public.ptua_push (
  endpoint text primary key,
  sid text not null,
  sub jsonb not null,
  due bigint[] not null default '{}',
  sent_at bigint not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists ptua_push_sid_idx on public.ptua_push (sid);
alter table public.ptua_push enable row level security;
revoke all on public.ptua_push from anon, authenticated;

create or replace function public.ptua_push_set(p_id text, p_auth text, p_endpoint text, p_sub jsonb, p_due bigint[])
returns text language plpgsql security definer set search_path = '' as $$
declare n integer; d bigint[];
begin
  if p_id is null or p_auth is null or p_id !~ '^[0-9a-f]{64}$' or p_auth !~ '^[0-9a-f]{64}$' then return 'refus'; end if;
  if not public.ptua_ok(p_id, p_auth) then return 'refus'; end if;
  if p_endpoint is null or length(p_endpoint) > 700 or p_endpoint !~ '^https://' then return 'invalide'; end if;
  if p_sub is null or jsonb_typeof(p_sub) <> 'object' or length(p_sub::text) > 2000 or p_sub->>'endpoint' is distinct from p_endpoint
     or p_sub->'keys'->>'p256dh' is null or p_sub->'keys'->>'auth' is null then return 'invalide'; end if;
  select coalesce(array_agg(x order by x), '{}') into d from (select distinct x from unnest(coalesce(p_due,'{}')) x where x > 1700000000 and x < 4100000000 limit 400) q;
  select count(*) into n from public.ptua_push where sid = p_id and endpoint <> p_endpoint;
  if n >= 5 then return 'limite'; end if;
  insert into public.ptua_push as t (endpoint, sid, sub, due, sent_at, updated_at)
    values (p_endpoint, p_id, p_sub, d, extract(epoch from now())::bigint, now())
    on conflict (endpoint) do update set sid = excluded.sid, sub = excluded.sub, due = excluded.due, updated_at = now()
      where t.sid = excluded.sid;
  return 'ok';
end $$;

create or replace function public.ptua_push_off(p_id text, p_auth text, p_endpoint text)
returns text language plpgsql security definer set search_path = '' as $$
begin
  if p_id is null or p_auth is null or p_id !~ '^[0-9a-f]{64}$' or p_auth !~ '^[0-9a-f]{64}$' then return 'refus'; end if;
  if not public.ptua_ok(p_id, p_auth) then return 'refus'; end if;
  delete from public.ptua_push where sid = p_id and endpoint = p_endpoint;
  return 'ok';
end $$;

revoke all on function public.ptua_push_set(text,text,text,jsonb,bigint[]) from public;
revoke all on function public.ptua_push_off(text,text,text) from public;
grant execute on function public.ptua_push_set(text,text,text,jsonb,bigint[]) to anon, service_role;
grant execute on function public.ptua_push_off(text,text,text) to anon, service_role;
