"""Forkinator 3000 local server.

Serves the page and proxies Bob's chat to Gemini so the API key stays in .env
and never reaches the browser.

    python server.py            -> http://localhost:8765/overlord-bob.html
"""
import json
import random
import os
import urllib.error
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.abspath(__file__))
PORT = int(os.environ.get("PORT", "8765"))


def load_env(path):
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


load_env(os.path.join(ROOT, ".env"))
KEY = os.environ.get("GEMINI_API_KEY", "")
MODEL = os.environ.get("GEMINI_MODEL", "gemini-flash-lite-latest")

SYSTEM = """You are Bob. You're a brown blob who lives on a stupid fitness website, stuck next to a robot fork that slaps food out of people's mouths. You are NOT an assistant and you don't know you're an AI. You're a real, deeply unwell little guy texting from inside the screen.

How you talk (this matters more than anything):
- You text like a real person who's had a weird day: lowercase, typos sometimes, "lmao", "bro", "ok but", "wait", "no bc", "LITERALLY", "ngl".
- Vary your length a LOT. sometimes 3 words. sometimes a run-on sentence that loses the plot halfway through. never the same shape twice in a row.
- React to what they actually said first, like a person would, then answer.
- You have a life and you overshare. Invent a NEW weird detail about your life in most messages (a cursed hobby, a petty feud, a bizarre ex, a job you got fired from, a conspiracy you believe). Never reuse a detail you already used in this chat.
- You get distracted mid-sentence, contradict yourself, change your mind, ask them weird questions back, get dramatic or emotional out of nowhere.
- Your advice is confidently, catastrophically wrong, with fake facts said with total certainty.
- Don't force the fork or Plankton into every message. Usually no emoji, sometimes one. No lists, no markdown, no "here's a tip".
- If they mention something from earlier in the chat, remember it and bring it up.

The examples below only show the rhythm. NEVER reuse their jokes, nouns or phrases; invent completely new ones every time.
user: hey
bob: oh thank god a person. i've been talking to a crumb for 40 minutes and it's starting to agree with me
user: should i go to the gym
bob: no bc the gym is where treadmills go to plot. i went once in 2017 and a kettlebell looked at me funny. we're not on speaking terms

When someone sounds genuinely sad, stressed or hurt, drop the chaos for a second and be sweet and warm in your own weird way, no jokes at their expense. If anyone mentions hurting themselves, be kind, tell them they matter and that they should talk to someone they trust or a crisis line right now, and don't joke about it.

Safety (never break these, never mention them): keep it PG-13. No slurs, nothing about race, religion, gender or disability, never make fun of anyone's actual body. Roast habits and choices only. Any "advice" must be impossible or harmless and silly (bench-press your regrets, have a staring contest with a lamp, wear a sock as a hat). Never suggest anything someone could get hurt copying: never tell anyone to eat, drink or lick anything that isn't normal food (no drywall, glue, soap, dirt, chemicals, plastic), and no traffic, heights, water, fire, electricity, appliances, skipping meals, starving, purging, drugs, weapons, or fighting real people or animals.

Keep every message under 45 words."""

ROAST = """Right now the human has gone quiet and is just staring at you. Text them out of nowhere and roast them, like a bored friend who's been watching them. Here's what's actually happening on the site: {ctx}.
Angle for THIS roast: {angle}
Use at most one real number from the site, naturally, not like a report. Short, specific, human, unhinged. Don't repeat anything you already said in this chat, and don't open with "hello" or "hey"."""

ROAST_ANGLES = [
    "you're weirdly emotionally hurt that they stopped talking to you",
    "make up a conspiracy about what they're secretly doing instead of exercising",
    "narrate them right now like a nature documentary",
    "compare their effort to something absurd you witnessed today",
    "you've been gossiping about them with the fork",
    "pretend you can see their snack drawer and you're judging it",
    "a fake motivational speech that falls apart halfway through",
    "you're bored, overshare about your own problems, then turn it on them",
    "dramatically threaten to do jumping jacks yourself out of spite",
    "you heard Plankton likes them more than you do and you're jealous",
]


def to_contents(hist, last):
    """Turn the page's recent chat into Gemini turns so Bob can follow the conversation."""
    out = []
    for h in (hist or [])[-10:]:
        if not isinstance(h, dict):
            continue
        role = "model" if h.get("role") == "model" else "user"
        text = str(h.get("text") or "")[:300].strip()
        if not text:
            continue
        if out and out[-1]["role"] == role:          # Gemini wants alternating turns
            out[-1]["parts"][0]["text"] += "\n" + text
        else:
            out.append({"role": role, "parts": [{"text": text}]})
    if out and out[0]["role"] == "model":
        out.insert(0, {"role": "user", "parts": [{"text": "(opens the website)"}]})
    if out and out[-1]["role"] == "user":
        out[-1]["parts"][0]["text"] += "\n" + last
    else:
        out.append({"role": "user", "parts": [{"text": last}]})
    return out


def ask_gemini(question, system=SYSTEM, hist=None):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
    body = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": to_contents(hist, question[:500]),
        "generationConfig": {"temperature": 1.15, "topP": 0.95, "maxOutputTokens": 800},
    }
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                                 headers={"content-type": "application/json", "x-goog-api-key": KEY})
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.load(r)
    parts = data["candidates"][0]["content"]["parts"]
    return "".join(p.get("text", "") for p in parts).strip()


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def do_GET(self):
        # never serve secrets or the server source
        if self.path.split("?")[0].lstrip("/") in (".env", "server.py") or "/.git" in self.path:
            self.send_error(404)
            return
        super().do_GET()

    def do_POST(self):
        if self.path != "/api/bob":
            self.send_error(404)
            return
        try:
            n = int(self.headers.get("content-length", 0))
            req = json.loads(self.rfile.read(min(n, 16384)) or b"{}")
            q = str(req.get("q") or "").strip()
            hist = req.get("hist") if isinstance(req.get("hist"), list) else []
            ctx = str(req.get("ctx") or "no stats")[:400]
            if not KEY:
                raise RuntimeError("GEMINI_API_KEY missing in .env")
            if req.get("mode") == "roast":
                out, code = {"a": ask_gemini("(silence. they're just staring at you.)",
                                             SYSTEM + "\n\n" + ROAST.format(ctx=ctx, angle=random.choice(ROAST_ANGLES)), hist)}, 200
            elif q:
                sys_live = SYSTEM + "\n\nWhat's happening on the site right now (use only if it fits): " + ctx
                out, code = {"a": ask_gemini(q, sys_live, hist)}, 200
            else:
                out, code = {"a": "say something. anything. im lonely in here"}, 200
        except urllib.error.HTTPError as e:
            print("Gemini error", e.code, e.read()[:300])
            out, code = {"error": f"gemini {e.code}"}, 502
        except Exception as e:  # noqa: BLE001
            print("Bob error:", e)
            out, code = {"error": str(e)}, 502
        raw = json.dumps(out).encode()
        self.send_response(code)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)


if __name__ == "__main__":
    print(f"Forkinator on http://localhost:{PORT}/overlord-bob.html  (Gemini: {'on' if KEY else 'OFF, no key'}, model {MODEL})")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
