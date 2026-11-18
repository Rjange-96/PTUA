// Agent IA cybersécurité pour le Gestionnaire PTUA — Supabase Edge Function (Deno)
// Accès : clé de synchronisation PTUA (id + auth), vérifiée par la fonction SQL ptua_agent_gate.
// Rien n'est stocké : ni les questions, ni les réponses.
// Boucle d'agent : le modèle (Gemini gratuit par défaut) raisonne, appelle des outils, puis répond.

const LLM_API_KEY = Deno.env.get("GEMINI_API_KEY") ?? Deno.env.get("LLM_API_KEY") ?? "";
const LLM_BASE_URL = (Deno.env.get("LLM_BASE_URL") ?? "https://generativelanguage.googleapis.com/v1beta/openai").replace(/\/$/, "");
const MODELS = (Deno.env.get("AGENT_MODEL") ?? "gemini-3.5-flash-lite,gemini-3.8-flash,gemini-3.6-flash").split(",").map((m) => m.trim()).filter(Boolean);
const LLM_TIMEOUT_MS = 20000; // par tentative
const ALLOWED_ORIGIN = Deno.env.get("ALLOWED_ORIGIN") ?? "*";
const MAX_STEPS = 6; // garde-fou : nombre max d'allers-retours outil
const HISTORY_LIMIT = 10; // messages d'historique acceptés du client
const MAX_INPUT_CHARS = 4000;

const CORS = {
  "Access-Control-Allow-Origin": ALLOWED_ORIGIN,
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

const SYSTEM = `Tu es CyberGuide, un assistant de cybersécurité DÉFENSIVE intégré au Gestionnaire PTUA (application de suivi de marchés publics). Tu n'as accès à aucune donnée de l'application.
Tu parles français, de façon claire et précise, avec des étapes concrètes.

Rôle : aider à protéger comptes, appareils, réseaux, sites et applications ; expliquer les menaces (phishing, ransomware, fuites de données...) ; analyser des liens suspects ; expliquer des vulnérabilités (CVE) ; guider l'apprentissage du hacking éthique (CTF, TryHackMe, laboratoires personnels).

Règles :
- Utilise tes outils quand ils apportent une information vérifiable (analyse d'URL, CVE, checklist). Ne devine pas un score ou une description de CVE.
- Ne demande jamais de mot de passe réel. Si l'utilisateur en colle un, dis-lui de le considérer comme compromis et de le changer, et de ne plus jamais l'écrire dans une conversation.
- Refuse d'aider à attaquer des systèmes sans autorisation, à créer des malwares, à voler des identifiants ou à surveiller quelqu'un. Propose à la place une alternative légale (labo local, plateforme d'entraînement, test sur ses propres systèmes).
- Si tu ne sais pas ou si l'outil échoue, dis-le honnêtement.
- Réponses courtes et structurées (l'utilisateur est souvent sur téléphone).`;

// ---------- Outils exposés au modèle ----------
const TOOLS = [
  {
    name: "analyze_url",
    description:
      "Analyse heuristique d'une URL pour repérer des signes de phishing (sans la visiter). Retourne un score de risque et les raisons.",
    input_schema: {
      type: "object",
      properties: { url: { type: "string", description: "L'URL complète à analyser" } },
      required: ["url"],
    },
  },
  {
    name: "lookup_cve",
    description:
      "Récupère la description officielle, le score CVSS et la gravité d'une vulnérabilité depuis la base NVD du NIST. Format : CVE-2024-12345.",
    input_schema: {
      type: "object",
      properties: { cve_id: { type: "string", description: "Identifiant CVE, ex. CVE-2021-44228" } },
      required: ["cve_id"],
    },
  },
  {
    name: "security_checklist",
    description:
      "Retourne une checklist de durcissement vérifiée pour un sujet donné.",
    input_schema: {
      type: "object",
      properties: {
        topic: {
          type: "string",
          enum: ["compte_en_ligne", "smartphone", "wifi_maison", "site_web", "application_supabase"],
        },
      },
      required: ["topic"],
    },
  },
] as const;

const CHECKLISTS: Record<string, string[]> = {
  compte_en_ligne: [
    "Mot de passe unique et long (gestionnaire de mots de passe), jamais réutilisé",
    "Double authentification par application (TOTP) ou clé physique, pas par SMS si possible",
    "Vérifier les appareils et sessions connectés, révoquer les inconnus",
    "Mettre à jour l'e-mail et le numéro de récupération",
    "Ne jamais saisir ses identifiants après avoir cliqué sur un lien reçu : passer par l'app ou le site tapé à la main",
  ],
  smartphone: [
    "Mises à jour du système et des applications activées",
    "Code de verrouillage de 6 chiffres ou plus + biométrie",
    "N'installer que depuis la boutique officielle ; auditer les autorisations des apps",
    "Activer la localisation/effacement à distance",
    "Désactiver Bluetooth/Wi-Fi automatique dans les lieux publics, éviter les Wi-Fi ouverts sans VPN",
  ],
  wifi_maison: [
    "Changer le mot de passe d'administration de la box",
    "WPA3 si disponible, sinon WPA2-AES ; mot de passe Wi-Fi long",
    "Désactiver WPS",
    "Mettre à jour le firmware de la box",
    "Réseau invité séparé pour les objets connectés (clim, caméras...)",
  ],
  site_web: [
    "HTTPS partout avec redirection automatique et HSTS",
    "En-têtes de sécurité : Content-Security-Policy, X-Content-Type-Options, frame-ancestors",
    "Requêtes paramétrées, jamais de SQL concaténé ; valider toutes les entrées",
    "Dépendances à jour (audit régulier) ; secrets hors du dépôt Git",
    "Sauvegardes testées et journaux d'accès surveillés",
  ],
  application_supabase: [
    "Row Level Security activée sur TOUTES les tables exposées, avec des policies précises",
    "La clé service_role ne doit jamais être dans le code côté client",
    "Secrets (clé API IA, etc.) uniquement dans les secrets des Edge Functions",
    "Vérifier l'utilisateur (auth.getUser) dans chaque Edge Function",
    "Limiter les appels (rate limiting) et restreindre les origines CORS",
    "Lancer l'outil de conseils de sécurité du tableau de bord Supabase (Advisors)",
  ],
};

function analyzeUrl(raw: string) {
  const reasons: string[] = [];
  let score = 0;
  let u: URL;
  try {
    u = new URL(raw.trim());
  } catch {
    return { valid: false, error: "URL invalide ou incomplète (ajouter https://)" };
  }
  const host = u.hostname.toLowerCase();
  const add = (pts: number, why: string) => { score += pts; reasons.push(why); };

  if (u.protocol !== "https:") add(2, "Pas de HTTPS (connexion non chiffrée)");
  if (/^\d{1,3}(\.\d{1,3}){3}$/.test(host)) add(3, "Adresse IP à la place d'un nom de domaine");
  if (host.includes("xn--")) add(3, "Domaine en punycode (peut imiter des caractères connus)");
  if (u.username || raw.includes("@")) add(3, "Contient un @ ou des identifiants dans l'URL (technique de dissimulation)");
  if (host.split(".").length > 4) add(2, "Beaucoup de sous-domaines");
  if (/\.(zip|mov|xyz|top|click|work|gq|tk|ml|cf|ga)$/.test(host)) add(2, "Extension de domaine souvent abusée");
  if (/(login|verify|secure|account|update|wallet|bank|support|confirm)/.test(host)) add(2, "Mots d'hameçonnage dans le nom de domaine");
  if (/^(bit\.ly|tinyurl\.com|t\.co|goo\.gl|is\.gd|cutt\.ly|rb\.gy)$/.test(host)) add(2, "Lien raccourci : destination cachée");
  if (raw.length > 120) add(1, "URL très longue");
  if ((host.match(/-/g) ?? []).length >= 3) add(1, "Nombreux tirets dans le domaine");

  const level = score >= 6 ? "élevé" : score >= 3 ? "moyen" : "faible";
  return {
    valid: true,
    host,
    risk_score: score,
    risk_level: level,
    reasons: reasons.length ? reasons : ["Aucun signal heuristique détecté"],
    note: "Analyse heuristique uniquement : un score faible ne garantit pas que le site est sûr.",
  };
}

async function lookupCve(id: string) {
  const cve = id.trim().toUpperCase();
  if (!/^CVE-\d{4}-\d{4,7}$/.test(cve)) return { error: "Format invalide, attendu CVE-AAAA-NNNN" };
  const r = await fetch(
    `https://services.nvd.nist.gov/rest/json/cves/2.0?cveId=${encodeURIComponent(cve)}`,
    { signal: AbortSignal.timeout(8000) },
  );
  if (!r.ok) return { error: `NVD a répondu ${r.status}` };
  const data = await r.json();
  const item = data.vulnerabilities?.[0]?.cve;
  if (!item) return { error: "CVE introuvable dans NVD" };
  const m = item.metrics ?? {};
  const cvss = (m.cvssMetricV31 ?? m.cvssMetricV40 ?? m.cvssMetricV30 ?? [])[0]?.cvssData;
  return {
    id: cve,
    description: item.descriptions?.find((d: { lang: string }) => d.lang === "en")?.value ?? "N/A",
    cvss_score: cvss?.baseScore ?? null,
    severity: cvss?.baseSeverity ?? null,
    published: item.published,
    source: "NVD (NIST)",
  };
}

async function runTool(name: string, input: Record<string, unknown>) {
  switch (name) {
    case "analyze_url": return analyzeUrl(String(input.url ?? ""));
    case "lookup_cve": return await lookupCve(String(input.cve_id ?? ""));
    case "security_checklist": {
      const list = CHECKLISTS[String(input.topic ?? "")];
      return list ? { items: list } : { error: "Sujet inconnu" };
    }
    default: return { error: `Outil inconnu : ${name}` };
  }
}

// ---------- Appel au modèle (format compatible OpenAI : Gemini gratuit, Groq...) ----------
class QuotaError extends Error {}

const LLM_TOOLS = TOOLS.map((t) => ({
  type: "function",
  function: { name: t.name, description: t.description, parameters: t.input_schema },
}));

// Plusieurs modèles gratuits, du plus rapide au plus complet : si l'un est lent, saturé ou refusé, on passe au suivant.
let preferred = 0;

async function callLLM(messages: unknown[]) {
  let quota = false;
  let last: unknown = new Error("Aucun modèle disponible");
  for (let n = 0; n < MODELS.length; n++) {
    const i = (preferred + n) % MODELS.length;
    const model = MODELS[i];
    for (const effort of ["low", null]) {
      const t0 = Date.now();
      try {
        const payload: Record<string, unknown> = { model, max_tokens: 1500, messages, tools: LLM_TOOLS, tool_choice: "auto" };
        if (effort) payload.reasoning_effort = effort;
        const r = await fetch(`${LLM_BASE_URL}/chat/completions`, {
          method: "POST",
          headers: { "content-type": "application/json", authorization: `Bearer ${LLM_API_KEY}` },
          body: JSON.stringify(payload),
          signal: AbortSignal.timeout(LLM_TIMEOUT_MS),
        });
        if (r.ok) {
          const data = await r.json();
          const msg = data.choices?.[0]?.message;
          if (!msg) throw new Error("Réponse du modèle vide");
          console.log(`llm ok ${model} ${Date.now() - t0}ms`);
          preferred = i;
          return msg;
        }
        const detail = (await r.text()).slice(0, 300);
        console.error(`llm ${model} HTTP ${r.status} ${Date.now() - t0}ms: ${detail}`);
        last = new Error(`LLM ${r.status}`);
        if (r.status === 429) quota = true;
        if (r.status === 400 && effort) continue; // réessai sans le réglage de réflexion
        break; // modèle suivant
      } catch (e) {
        console.error(`llm ${model} ${(e as Error).name} ${Date.now() - t0}ms`);
        last = e;
        break; // modèle suivant
      }
    }
  }
  if (quota) throw new QuotaError("quota");
  throw last;
}

// Boucle d'agent : raisonner -> appeler outils -> répondre
async function runAgent(history: { role: string; content: unknown }[]) {
  const messages: unknown[] = [{ role: "system", content: SYSTEM }, ...history];
  const toolsUsed: string[] = [];
  for (let step = 0; step < MAX_STEPS; step++) {
    const msg = await callLLM(messages);
    // On renvoie le message tel quel : il porte les "thought signatures" exigées par Gemini 3
    messages.push(msg);
    const calls = msg.tool_calls ?? [];
    if (!calls.length) {
      const text = typeof msg.content === "string" ? msg.content.trim() : "";
      return { reply: text || "(réponse vide)", toolsUsed };
    }
    for (const call of calls) {
      const name = call.function?.name ?? "";
      toolsUsed.push(name);
      let out: unknown;
      try {
        const args = call.function?.arguments ? JSON.parse(call.function.arguments) : {};
        out = await runTool(name, args);
      } catch (e) { out = { error: (e as Error).message }; }
      messages.push({ role: "tool", tool_call_id: call.id, content: JSON.stringify(out) });
    }
  }
  return { reply: "J'ai atteint ma limite d'étapes. Reformule ou précise ta question.", toolsUsed };
}

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { ...CORS, "content-type": "application/json" } });

const HEX64 = /^[0-9a-f]{64}$/;
// Clé publique de l'application (la même que dans le code public de PTUA) : sert seulement à appeler ptua_agent_gate.
const PUB_KEY = Deno.env.get("PTUA_PUBLISHABLE_KEY") ?? "sb_publishable_sFlCanmeyZ_iOQJ6zynyqA_qPgTsUey";

async function gate(id: string, auth: string): Promise<string> {
  const r = await fetch(`${Deno.env.get("SUPABASE_URL")}/rest/v1/rpc/ptua_agent_gate`, {
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

  // 1) Validation de l'entrée
  let body: Record<string, unknown>;
  try { body = await req.json(); } catch { return json({ error: "Corps JSON invalide" }, 400); }
  const id = String(body?.id ?? ""), auth = String(body?.auth ?? "");
  if (!HEX64.test(id) || !HEX64.test(auth)) return json({ error: "Accès refusé" }, 401);
  const message = String(body?.message ?? "").trim();
  if (!message) return json({ error: "Message vide" }, 400);
  if (message.length > MAX_INPUT_CHARS) return json({ error: "Message trop long" }, 400);
  const history: { role: string; content: string }[] = [];
  if (Array.isArray(body?.history)) {
    for (const m of body.history.slice(-HISTORY_LIMIT)) {
      const role = m?.role === "assistant" ? "assistant" : m?.role === "user" ? "user" : "";
      const content = typeof m?.content === "string" ? m.content.slice(0, MAX_INPUT_CHARS) : "";
      if (role && content) history.push({ role, content });
    }
    while (history.length && history[0].role !== "user") history.shift();
  }

  // 2) Accès (clé de synchronisation) + limite de débit
  try {
    const g = await gate(id, auth);
    if (g === "limite") return json({ error: "Trop de questions cette heure-ci, réessayez plus tard" }, 429);
    if (g !== "ok") return json({ error: "Accès refusé" }, 401);
  } catch (e) {
    console.error(e);
    return json({ error: "Vérification d'accès impossible" }, 500);
  }
  if (!LLM_API_KEY) return json({ error: "Clé GEMINI_API_KEY manquante : ajoutez-la dans les secrets des Edge Functions" }, 500);

  // 3) Agent
  try {
    const { reply, toolsUsed } = await runAgent([...history, { role: "user", content: message }]);
    return json({ reply, tools_used: toolsUsed });
  } catch (e) {
    if (e instanceof QuotaError) return json({ error: "Quota gratuit atteint, réessayez dans une minute" }, 429);
    console.error(e);
    return json({ error: "L'agent a rencontré une erreur" }, 500);
  }
});
