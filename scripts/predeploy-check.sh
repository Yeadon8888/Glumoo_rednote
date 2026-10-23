#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$PROJECT_ROOT"
uv sync --locked
uv run pytest -q
uv run python -m py_compile backend/errors.py backend/routes/*.py backend/generators/*.py backend/services/*.py

cd "$PROJECT_ROOT/frontend"
pnpm install --frozen-lockfile
pnpm typecheck
pnpm build

echo "Pre-deploy checks passed."
