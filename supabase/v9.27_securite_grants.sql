-- v9.27 — audit : retrait des accès inutiles (appliqué sur le projet de production le 2026-11-18).
-- Seul le rôle « anon » (clé publique de l'application et des Edge Functions) appelle ces fonctions.
revoke execute on function public.ptua_pv_gate(text, text) from public, authenticated;
revoke execute on function public.ptua_push_set(text, text, text, jsonb, bigint[]) from public, authenticated;
revoke execute on function public.ptua_push_off(text, text, text) from public, authenticated;
-- Table de démonstration « garanties » (0 ligne, non utilisée par l'application).
revoke all on table public.garanties from authenticated, anon;
