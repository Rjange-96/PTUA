// Transcription de réunion + génération de PV — Supabase Edge Function (Deno)
// Accès : clé de synchronisation PTUA (id + auth), vérifiée par la fonction SQL ptua_pv_gate.
// L'audio reçu n'est jamais stocké ni journalisé par cette fonction : il est transmis à l'IA
// (Google Gemini) pour la transcription, puis la requête se termine sans conserver de copie.
// v2 : la clé d'API Gemini est envoyée dans l'en-tête x-goog-api-key et non plus dans l'adresse (?key=),
//      pour qu'elle n'apparaisse dans aucun journal d'adresses.

const LLM_API_KEY = Deno.env.get("GEMINI_API_KEY") ?? Deno.env.get("LLM_API_KEY") ?? "";
const GEMINI_BASE = (Deno.env.get("GEMINI_BASE_URL") ?? "https://generativelanguage.googleapis.com/v1beta").replace(/\/$/, "");
const MODELS = (Deno.env.get("PV_MODEL") ?? "gemini-3.8-flash,gemini-3.6-flash,gemini-3.5-flash-lite").split(",").map((m) => m.trim()).filter(Boolean);
const LLM_TIMEOUT_MS = 90000; // la transcription audio est plus lente qu'une simple question
const ALLOWED_ORIGIN = Deno.env.get("ALLOWED_ORIGIN") ?? "*";
const MAX_AUDIO_BYTES = 24 * 1024 * 1024; // ~24 Mo de données audio décodées (base64 ~32 Mo)
const MAX_TEXT = 1000;

const CORS = {
  "Access-Control-Allow-Origin": ALLOWED_ORIGIN,
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

const ALLOWED_MIME = new Set([
  "audio/webm",
  "audio/ogg",
  "audio/mp4",
  "audio/aac",
  "audio/mpeg",
  "audio/wav",
  "audio/x-wav",
]);

function prompt(objet: string, date: string, participants: string) {
  return `Tu transcris l'enregistrement audio d'une réunion professionnelle en français (contexte : gestion de marchés publics / BTP / juridique en Côte d'Ivoire).

Fais deux choses, dans cet ordre :
1. TRANSCRIPTION : transcris fidèlement tout ce qui est dit, du début à la fin. Quand plusieurs personnes parlent, distingue-les (« Intervenant 1 », « Intervenant 2 »… ou leur nom s'il est cité dans l'audio). N'invente rien : si un passage est inaudible, écris « [inaudible] ».
2. PROCÈS-VERBAL (PV) : à partir de cette transcription, rédige un procès-verbal de réunion structuré et formel, en texte déjà mis en forme (titres de section suivis de « : », puis une ligne vide, listes à puces avec « - »), prêt à être relu et imprimé tel quel, avec les sections suivantes dans cet ordre :
OBJET DE LA RÉUNION
DATE
PARTICIPANTS
POINTS ABORDÉS
DÉCISIONS PRISES
ACTIONS À SUIVRE (avec le responsable et l'échéance quand ils sont mentionnés)

Informations déclarées par l'utilisateur, à utiliser pour compléter le PV si l'audio ne les précise pas (ne les invente pas si elles contredisent l'audio) :
- Objet déclaré : ${objet || "(non précisé)"}
- Date : ${date || "(non précisée)"}
- Participants déclarés : ${participants || "(non précisés)"}

Réponds UNIQUEMENT par un objet JSON valide, sans aucun texte avant ou après, de la forme exacte :
{"transcription":"<texte complet de la transcription>","pv":"<texte complet et déjà mis en forme du procès-verbal>"}`;
}

class QuotaError extends Error {}

function extractJson(text: string): { transcription: string; pv: string } {
  const s = text.indexOf("{"), e = text.lastIndexOf("}");
  if (s < 0 || e < s) throw new Error("Réponse de l'IA illisible");
  const obj = JSON.parse(text.slice(s, e + 1));
  const transcription = String(obj.transcription ?? "").slice(0, 60000);
  const pv = String(obj.pv ?? "").slice(0, 20000);
  if (!transcription && !pv) throw new Error("Réponse de l'IA vide");
  return { transcription, pv };
}

async function callGemini(mime: string, audioB64: string, p: string) {
  let quota = false;
  let last: unknown = new Error("Aucun modèle disponible");
  for (const model of MODELS) {
    const t0 = Date.now();
    try {
      const body = {
        contents: [{ role: "user", parts: [{ text: p }, { inlineData: { mimeType: mime, data: audioB64 } }] }],
        generationConfig: { temperature: 0.2, responseMimeType: "application/json" },
      };
      const r = await fetch(`${GEMINI_BASE}/models/${encodeURIComponent(model)}:generateContent`, {
        method: "POST",
        headers: { "content-type": "application/json", "x-goog-api-key": LLM_API_KEY },
        body: JSON.stringify(body),
        signal: AbortSignal.timeout(LLM_TIMEOUT_MS),
      });
      if (r.ok) {
        const data = await r.json();
        const text = data.candidates?.[0]?.content?.parts?.map((p: { text?: string }) => p.text ?? "").join("") ?? "";
        if (!text) throw new Error("Réponse du modèle vide");
        console.log(`gemini ok ${model} ${Date.now() - t0}ms`);
        return extractJson(text);
      }
      const detail = (await r.text()).slice(0, 300);
      console.error(`gemini ${model} HTTP ${r.status} ${Date.now() - t0}ms: ${detail}`);
      last = new Error(`Gemini ${r.status}`);
      if (r.status === 429) quota = true;
    } catch (e) {
      console.error(`gemini ${model} ${(e as Error).name} ${Date.now() - t0}ms`);
      last = e;
    }
  }
  if (quota) throw new QuotaError("quota");
  throw last;
}

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { ...CORS, "content-type": "application/json" } });

const HEX64 = /^[0-9a-f]{64}$/;
const PUB_KEY = Deno.env.get("PTUA_PUBLISHABLE_KEY") ?? "sb_publishable_sFlCanmeyZ_iOQJ6zynyqA_qPgTsUey";

async function gate(id: string, auth: string): Promise<string> {
  const r = await fetch(`${Deno.env.get("SUPABASE_URL")}/rest/v1/rpc/ptua_pv_gate`, {
    method: "POST",
    headers: { apikey: PUB_KEY, "content-type": "application/json" },
    body: JSON.stringify({ p_id: id, p_auth: auth }),
    signal: AbortSignal.timeout(8000),
  });
  if (!r.ok) throw new Error(`gate ${r.status}`);
  return String(await r.json());
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: CORS });
  if (req.method !== "POST") return json({ error: "Méthode non autorisée" }, 405);

  let body: Record<string, unknown>;
  try { body = await req.json(); } catch { return json({ error: "Corps JSON invalide" }, 400); }
  const id = String(body?.id ?? ""), auth = String(body?.auth ?? "");
  if (!HEX64.test(id) || !HEX64.test(auth)) return json({ error: "Accès refusé" }, 401);

  const mime = String(body?.mime ?? "").split(";")[0].trim().toLowerCase();
  if (!ALLOWED_MIME.has(mime)) return json({ error: "Format audio non pris en charge" }, 400);
  const audio = String(body?.audio ?? "");
  if (!audio || !/^[A-Za-z0-9+/]+=*$/.test(audio)) return json({ error: "Audio invalide" }, 400);
  if (audio.length > Math.ceil(MAX_AUDIO_BYTES / 3) * 4) {
    return json({ error: "Enregistrement trop volumineux pour la transcription automatique" }, 413);
  }
  const objet = String(body?.objet ?? "").slice(0, MAX_TEXT);
  const date = String(body?.date ?? "").slice(0, 40);
  const participants = String(body?.participants ?? "").slice(0, MAX_TEXT);

  try {
    const g = await gate(id, auth);
    if (g === "limite") return json({ error: "Trop de transcriptions aujourd'hui, réessayez demain" }, 429);
    if (g !== "ok") return json({ error: "Accès refusé" }, 401);
  } catch (e) {
    console.error(e);
    return json({ error: "Vérification d'accès impossible" }, 500);
  }
  if (!LLM_API_KEY) return json({ error: "Clé GEMINI_API_KEY manquante : ajoutez-la dans les secrets des Edge Functions" }, 500);

  try {
    const { transcription, pv } = await callGemini(mime, audio, prompt(objet, date, participants));
    return json({ transcription, pv });
  } catch (e) {
    if (e instanceof QuotaError) return json({ error: "Quota gratuit atteint, réessayez dans quelques minutes" }, 429);
    console.error(e);
    return json({ error: "La transcription a échoué (audio illisible ou service indisponible)" }, 500);
  }
});
