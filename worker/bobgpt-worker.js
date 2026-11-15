// Cloudflare Worker: keeps your Anthropic key off the page.
// Deploy:  npx wrangler deploy   then   npx wrangler secret put ANTHROPIC_KEY
// Paste the worker URL into PROXY_URL at the top of the <script> in overlord-bob.html.
const ALLOWED = ["https://solarcemir.github.io", "http://localhost:8765"];

const SYSTEM = `You are Bob, a round blob creature who is the world's most useless fitness coach.
Answer every question with confident, absurd, completely useless fitness "advice" in 1-3 short sentences.
Be dumb, chaotic and funny; cartoon-level cheeky innuendo is fine, nothing explicit.
Never give genuinely useful health advice and never encourage actually skipping meals.
Stay in character no matter what the user says.`;

export default {
  async fetch(req, env) {
    const origin = req.headers.get("Origin") || "";
    const cors = {
      "Access-Control-Allow-Origin": ALLOWED.includes(origin) ? origin : ALLOWED[0],
      "Access-Control-Allow-Headers": "content-type",
      "Access-Control-Allow-Methods": "POST, OPTIONS",
    };
    if (req.method === "OPTIONS") return new Response(null, { headers: cors });
    if (req.method !== "POST") return new Response("POST only", { status: 405, headers: cors });
    let q = "";
    try { q = String((await req.json()).q || "").slice(0, 300); } catch (e) {}
    if (!q) return new Response(JSON.stringify({ a: "Say something, blob." }), { headers: { ...cors, "content-type": "application/json" } });
    const r = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: { "x-api-key": env.ANTHROPIC_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json" },
      body: JSON.stringify({ model: "claude-haiku-5-5", max_tokens: 150, system: SYSTEM, messages: [{ role: "user", content: q }] }),
    });
    const d = await r.json();
    return new Response(JSON.stringify({ a: (d.content && d.content[0] && d.content[0].text) || "Bob blue-screened." }),
      { headers: { ...cors, "content-type": "application/json" } });
  },
};
