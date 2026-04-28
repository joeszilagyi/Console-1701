#!/usr/bin/env bash
set -euo pipefail

if [[ -x .venv/bin/console-1706 ]]; then
  .venv/bin/console-1706 scan "$@"
else
  console-1706 scan "$@"
fi
