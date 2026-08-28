#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

command -v uv >/dev/null 2>&1 || {
  echo "uv is required. Install it from https://docs.astral.sh/uv/ and rerun this script."
  exit 1
}

uv python pin 3.12
uv sync

if [[ ! -f .env && -f .env.example ]]; then
  cp .env.example .env
  echo "Created .env from .env.example; add your API keys if needed."
fi

echo "Agent Lab environment ready."
echo "Run: uv run pytest"
echo "Run: PYTHONPATH=. uv run python experiments/memory/01_basic/main.py"
