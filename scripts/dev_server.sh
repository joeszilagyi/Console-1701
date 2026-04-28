#!/usr/bin/env bash
set -euo pipefail

if [[ ! -x .venv/bin/console-1706 ]]; then
  python3 -m venv .venv
  . .venv/bin/activate
  python -m pip install -e '.[dev]'
else
  . .venv/bin/activate
fi

console-1706 init-config
console-1706 serve
