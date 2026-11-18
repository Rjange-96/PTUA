-- v9.22 — durcissement des rappels (déjà appliqué sur le projet de production ; copie conservée ici pour mémoire).
-- Liste blanche des services de notification : empêche d'enregistrer une adresse arbitraire que le serveur contacterait.
create or replace function public.ptua_push_host_ok(p_endpoint text) returns boolean
language sql immutable set search_path = '' as $$
  select p_endpoint ~ '^https://(web\.push\.apple\.com|fcm\.googleapis\.com|updates\.push\.services\.mozilla\.com|[a-z0-9-]+\.notify\.windows\.com)/[^\s]*$';
$$;
create or replace function public.ptua_push_due(p_now bigint) returns table(endpoint text, sub jsonb)
language sql stable security definer set search_path = '' as $$
  select p.endpoint, p.sub from public.ptua_push p
  where exists(select 1 from unnest(p.due) d where d > p.sent_at and d <= p_now)
  order by p.sent_at limit 500;
$$;
create or replace function public.ptua_push_purge(p_now bigint) returns integer
language sql security definer set search_path = '' as $$
  with x as (delete from public.ptua_push p
    where p_now - p.sent_at > 90*86400 and not exists(select 1 from unnest(p.due) d where d > p_now) returning 1)
  select count(*)::integer from x;
$$;
revoke all on function public.ptua_push_host_ok(text), public.ptua_push_due(bigint), public.ptua_push_purge(bigint) from public, anon, authenticated;
-- ptua_push_set (version actuelle) : liste blanche + plafond global de 2000 abonnements. Voir la définition en production.
