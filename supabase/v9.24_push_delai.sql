-- v9.24 — Rappels : délai d'attente de l'appel planifié porté de 5 s (valeur par défaut de pg_net) à 30 s.
-- Constat du 17/11/2026 : 18 appels sur 36 en 24 h abandonnés à 5 s (démarrage à froid de la fonction ptua-push).
-- Les clés restent lues dans ptua_push_cfg, jamais écrites ici. Appliqué sur le projet le 17/11/2026.
create or replace function public.ptua_push_tick() returns void language sql security definer set search_path = '' as $$
  select net.http_post(url:='https://iofbwpzhptctyelmylkz.supabase.co/functions/v1/ptua-push',
    headers:=jsonb_build_object('x-cron-key',(select v from public.ptua_push_cfg where k='cron_key')),
    timeout_milliseconds:=30000);
$$;
revoke all on function public.ptua_push_tick() from public, anon, authenticated;
