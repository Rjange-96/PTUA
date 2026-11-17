-- v9.22 — Durcissement des rappels sur le téléphone. À appliquer UNE fois, APRÈS v9.17_rappels_push.sql.
-- Ne supprime aucune donnée valide. Corrige deux faiblesses :
--  1) N'importe qui peut créer un espace de synchronisation, donc enregistrer des « adresses de notification » arbitraires :
--     le serveur envoyait alors des requêtes vers n'importe quel site https. Seuls les services de notification réels
--     (Apple, Google, Mozilla, Microsoft) sont désormais acceptés.
--  2) La fonction d'envoi ne lisait que 500 lignes, dans un ordre quelconque : en remplissant la table, un tiers pouvait
--     faire disparaître VOS rappels sans bruit. Elle ne lit plus que les lignes dont un rappel est dû, et la table est plafonnée.

-- Adresses de notification acceptées (hôtes officiels des navigateurs)
create or replace function public.ptua_push_host_ok(p_endpoint text) returns boolean
language sql immutable set search_path = '' as $$
  select p_endpoint ~ '^https://(web\.push\.apple\.com|fcm\.googleapis\.com|updates\.push\.services\.mozilla\.com|[a-z0-9-]+\.notify\.windows\.com)/[^\s]*$';
$$;
revoke all on function public.ptua_push_host_ok(text) from public, anon, authenticated;

-- Nettoyage des lignes déjà présentes qui ne pointent pas vers un service de notification
delete from public.ptua_push where not public.ptua_push_host_ok(endpoint);

create or replace function public.ptua_push_set(p_id text, p_auth text, p_endpoint text, p_sub jsonb, p_due bigint[])
returns text language plpgsql security definer set search_path = '' as $$
declare n integer; d bigint[];
begin
  if p_id is null or p_auth is null or p_id !~ '^[0-9a-f]{64}$' or p_auth !~ '^[0-9a-f]{64}$' then return 'refus'; end if;
  if not public.ptua_ok(p_id, p_auth) then return 'refus'; end if;
  if p_endpoint is null or length(p_endpoint) > 700 or not public.ptua_push_host_ok(p_endpoint) then return 'invalide'; end if;
  if p_sub is null or jsonb_typeof(p_sub) <> 'object' or length(p_sub::text) > 2000 or p_sub->>'endpoint' is distinct from p_endpoint
     or p_sub->'keys'->>'p256dh' is null or p_sub->'keys'->>'auth' is null then return 'invalide'; end if;
  select coalesce(array_agg(x order by x), '{}') into d from (select distinct x from unnest(coalesce(p_due,'{}')) x where x > 1700000000 and x < 4100000000 limit 400) q;
  select count(*) into n from public.ptua_push where sid = p_id and endpoint <> p_endpoint;
  if n >= 5 then return 'limite'; end if;
  -- plafond global : protège l'envoi des rappels contre le remplissage de la table
  if not exists(select 1 from public.ptua_push where endpoint = p_endpoint)
     and (select count(*) from public.ptua_push) >= 2000 then return 'limite'; end if;
  insert into public.ptua_push as t (endpoint, sid, sub, due, sent_at, updated_at)
    values (p_endpoint, p_id, p_sub, d, extract(epoch from now())::bigint, now())
    on conflict (endpoint) do update set sid = excluded.sid, sub = excluded.sub, due = excluded.due, updated_at = now()
      where t.sid = excluded.sid;
  return 'ok';
end $$;
revoke all on function public.ptua_push_set(text,text,text,jsonb,bigint[]) from public;
grant execute on function public.ptua_push_set(text,text,text,jsonb,bigint[]) to anon, service_role;

-- Lignes dont un rappel est dû maintenant (utilisé par la fonction d'envoi, jamais par l'application)
create or replace function public.ptua_push_due(p_now bigint)
returns table(endpoint text, sub jsonb) language sql stable security definer set search_path = '' as $$
  select p.endpoint, p.sub from public.ptua_push p
  where exists(select 1 from unnest(p.due) d where d > p.sent_at and d <= p_now)
  order by p.sent_at limit 500;
$$;
revoke all on function public.ptua_push_due(bigint) from public, anon, authenticated;
grant execute on function public.ptua_push_due(bigint) to service_role;

-- Lignes périmées (plus aucun rappel à venir depuis 90 jours)
create or replace function public.ptua_push_purge(p_now bigint) returns integer
language sql security definer set search_path = '' as $$
  with x as (delete from public.ptua_push p
    where p_now - p.sent_at > 90*86400 and not exists(select 1 from unnest(p.due) d where d > p_now) returning 1)
  select count(*)::integer from x;
$$;
revoke all on function public.ptua_push_purge(bigint) from public, anon, authenticated;
grant execute on function public.ptua_push_purge(bigint) to service_role;
