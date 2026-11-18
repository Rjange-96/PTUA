// Edge Function « ptua-push » (v9.17) : envoie une notification générique (aucun contenu de marché) aux téléphones
// dont un instant d'alerte vient d'arriver. Appelée toutes les 10 minutes par pg_cron avec l'en-tête x-cron-key.
// Les clés (VAPID, clé du planificateur) sont lues dans la table ptua_push_cfg, inaccessible depuis l'application.
import webpush from "npm:web-push@3.6.7";
import { createClient } from "npm:@supabase/supabase-js@2";
const sb = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
Deno.serve(async (req) => {
  const { data: cfg } = await sb.from("ptua_push_cfg").select("k,v");
  const C: Record<string, string> = {};
  (cfg || []).forEach((r: any) => (C[r.k] = r.v));
  const key = req.headers.get("x-cron-key") || "";
  if (!C.cron_key || key.length !== C.cron_key.length || key !== C.cron_key) return new Response("refus", { status: 401 });
  webpush.setVapidDetails("mailto:rjange96@gmail.com", C.vapid_public, C.vapid_private);
  const now = Math.floor(Date.now() / 1000);
  const { data: rows, error } = await sb.from("ptua_push").select("endpoint,sub,due,sent_at").limit(500);
  if (error) return new Response(JSON.stringify({ error: error.message }), { status: 500 });
  let sent = 0, gone = 0, fail = 0;
  for (const r of rows || []) {
    const hit = (r.due || []).some((d: number) => d > r.sent_at && d <= now);
    if (!hit) { if ((r.due || []).every((d: number) => d <= now) && now - r.sent_at > 90 * 86400) await sb.from("ptua_push").delete().eq("endpoint", r.endpoint); continue; }
    try {
      await webpush.sendNotification(r.sub, JSON.stringify({ t: "PTUA", b: "Des échéances demandent votre attention." }), { TTL: 6 * 3600, urgency: "normal" });
      sent++;
      await sb.from("ptua_push").update({ sent_at: now }).eq("endpoint", r.endpoint);
    } catch (e: any) {
      if (e && (e.statusCode === 404 || e.statusCode === 410)) { gone++; await sb.from("ptua_push").delete().eq("endpoint", r.endpoint); }
      else { fail++; await sb.from("ptua_push").update({ sent_at: now }).eq("endpoint", r.endpoint); }
    }
  }
  return new Response(JSON.stringify({ sent, gone, fail, total: (rows || []).length }), { headers: { "content-type": "application/json" } });
});
