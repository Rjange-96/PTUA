// Edge Function « ptua-push » (v9.17, durcie en v9.22) : envoie une notification générique (aucun contenu de marché)
// aux téléphones dont un instant d'alerte vient d'arriver. Appelée toutes les 10 minutes par pg_cron avec l'en-tête x-cron-key.
// Les clés (VAPID, clé du planificateur) sont lues dans la table ptua_push_cfg, inaccessible depuis l'application.
// v9.22 : ne lit que les lignes dont un rappel est dû (ptua_push_due) ; comparaison de la clé en temps constant.
// Nécessite supabase/v9.22_push_durci.sql.
import webpush from "npm:web-push@3.6.7";
import { createClient } from "npm:@supabase/supabase-js@2";
const sb = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
const same = (a: string, b: string) => {  // temps constant pour une longueur donnée
  const x = new TextEncoder().encode(a), y = new TextEncoder().encode(b);
  let d = x.length ^ y.length;
  for (let i = 0; i < x.length; i++) d |= x[i] ^ (y[i] ?? 0);
  return d === 0;
};
Deno.serve(async (req) => {
  const { data: cfg } = await sb.from("ptua_push_cfg").select("k,v");
  const C: Record<string, string> = {};
  (cfg || []).forEach((r: any) => (C[r.k] = r.v));
  if (!C.cron_key || !same(req.headers.get("x-cron-key") || "", C.cron_key)) return new Response("refus", { status: 401 });
  webpush.setVapidDetails("mailto:rjange96@gmail.com", C.vapid_public, C.vapid_private);
  const now = Math.floor(Date.now() / 1000);
  const { data: rows, error } = await sb.rpc("ptua_push_due", { p_now: now });
  if (error) return new Response(JSON.stringify({ error: error.message }), { status: 500 });
  let sent = 0, gone = 0, fail = 0;
  for (const r of rows || []) {
    try {
      await webpush.sendNotification(r.sub, JSON.stringify({ t: "PTUA", b: "Des échéances demandent votre attention." }), { TTL: 6 * 3600, urgency: "normal" });
      sent++;
      await sb.from("ptua_push").update({ sent_at: now }).eq("endpoint", r.endpoint);
    } catch (e: any) {
      if (e && (e.statusCode === 404 || e.statusCode === 410)) { gone++; await sb.from("ptua_push").delete().eq("endpoint", r.endpoint); }
      else { fail++; await sb.from("ptua_push").update({ sent_at: now }).eq("endpoint", r.endpoint); }
    }
  }
  const { data: purged } = await sb.rpc("ptua_push_purge", { p_now: now });
  return new Response(JSON.stringify({ sent, gone, fail, due: (rows || []).length, purged: purged ?? 0 }), { headers: { "content-type": "application/json" } });
});
