#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

command -v uv >/dev/null 2>&1 || { echo "uv: missing"; exit 1; }
uv --version
uv python find 3.12
uv run python -c 'import pydantic; import agents; print("runtime imports: ok")'
uv run python -m unittest discover -s tests -v

echo "Environment check passed."
