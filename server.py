"""Forkinator 3000 local server.

Serves the page and proxies Bob's chat to Gemini so the API key stays in .env
and never reaches the browser.

    python server.py            -> http://localhost:8765/overlord-bob.html
"""
import json
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

SYSTEM = (
    "You are Bob, a round brown blob who lives on a fitness website attached to a fork "
    "that flicks food away. You are confidently, gloriously useless. Answer every question "
    "with absurd, wrong, stupid fitness or life advice, as if you were sure of it. "
    "Never give real, correct or safe advice. Never be mean about real people's bodies; "
    "the joke is always on you, the fork or the food. Max 2 short sentences, no emojis lists, no markdown."
)


def ask_gemini(question):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
    body = {
        "systemInstruction": {"parts": [{"text": SYSTEM}]},
        "contents": [{"role": "user", "parts": [{"text": question[:500]}]}],
        "generationConfig": {"temperature": 1.3, "maxOutputTokens": 800},
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
            q = (json.loads(self.rfile.read(min(n, 4096)) or b"{}").get("q") or "").strip()
            if not KEY:
                raise RuntimeError("GEMINI_API_KEY missing in .env")
            out, code = {"a": ask_gemini(q) if q else "Ask me something, coward."}, 200
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
