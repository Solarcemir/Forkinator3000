#!/usr/bin/env sh
# Forkinator 3000 - run with: ./start.sh  (needs Python 3)
cd "$(dirname "$0")" || exit 1

if command -v python3 >/dev/null 2>&1; then PY=python3
elif command -v python >/dev/null 2>&1; then PY=python
else
  echo "Python 3 is not installed. Get it from https://www.python.org/downloads/ and run ./start.sh again."
  exit 1
fi

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env - add your Gemini key there for the real AI (optional)."
fi

exec "$PY" -u server.py
