#!/usr/bin/env bash
set -euo pipefail

# Run one local console-1706 scan from any working directory.
# Side effects: writes the configured console-1706 SQLite state and handoff/scan artifacts only.
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
PROJECT_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd -P)"
CONSOLE_CLI="$PROJECT_DIR/.venv/bin/console-1706"

usage() {
  cat <<'EOF'
Usage: scripts/scan_once.sh [--check] [--help] [-- SCAN_ARGS...]

Run `console-1706 scan` once. The scan uses local read-only probes, then writes
results to the configured console-1706 state database.

Options:
  --check  Show which console-1706 executable would be used without scanning.
  --help   Show this help.

Arguments after -- are forwarded to `console-1706 scan`.
EOF
}

check_only=false
scan_args=()
while (($#)); do
  case "$1" in
    --check)
      check_only=true
      shift
      ;;
    --help | -h)
      usage
      exit 0
      ;;
    --)
      shift
      scan_args+=("$@")
      break
      ;;
    *)
      scan_args+=("$1")
      shift
      ;;
  esac
done

cd "$PROJECT_DIR"

if [[ -x "$CONSOLE_CLI" ]]; then
  resolved_cli="$CONSOLE_CLI"
else
  resolved_cli="$(command -v console-1706 || true)"
fi

if [[ "$check_only" == true ]]; then
  printf 'Project: %s\n' "$PROJECT_DIR"
  if [[ -n "$resolved_cli" ]]; then
    printf 'CLI: %s\n' "$resolved_cli"
  else
    printf 'CLI: missing (console-1706)\n'
    exit 127
  fi
  exit 0
fi

if [[ -z "$resolved_cli" ]]; then
  printf 'error: console-1706 not found; run scripts/dev_server.sh --check first.\n' >&2
  exit 127
fi

exec "$resolved_cli" scan "${scan_args[@]}"
