#!/usr/bin/env bash
set -euo pipefail

# Start a local development server from any working directory.
# Side effects: creates/updates the repo-local .venv and default console-1701 config as needed.
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
PROJECT_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd -P)"
VENV_DIR="$PROJECT_DIR/.venv"
CONSOLE_CLI="$VENV_DIR/bin/console-1701"
PYTHON_BIN="${PYTHON_BIN:-python3}"

usage() {
  cat <<'EOF'
Usage: scripts/dev_server.sh [--check] [--help] [-- SERVE_ARGS...]

Bootstrap the repo-local .venv if needed, initialize the default config, then
run `console-1701 serve`. The application itself enforces 127.0.0.1 binding.

Options:
  --check  Show resolved paths and prerequisites without creating .venv or serving.
  --help   Show this help.

Arguments after -- are forwarded to `console-1701 serve`.
EOF
}

check_only=false
serve_args=()
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
      serve_args+=("$@")
      break
      ;;
    *)
      serve_args+=("$1")
      shift
      ;;
  esac
done

cd "$PROJECT_DIR"

if [[ "$check_only" == true ]]; then
  printf 'Project: %s\n' "$PROJECT_DIR"
  python_path="$(command -v "$PYTHON_BIN" || true)"
  if [[ -n "$python_path" ]]; then
    printf 'Python: %s\n' "$python_path"
  else
    printf 'Python: missing (%s)\n' "$PYTHON_BIN"
  fi
  if [[ -x "$CONSOLE_CLI" ]]; then
    printf 'CLI: %s\n' "$CONSOLE_CLI"
  else
    printf 'CLI: missing (%s)\n' "$CONSOLE_CLI"
  fi
  if [[ ! -x "$CONSOLE_CLI" && -z "$python_path" ]]; then
    printf 'error: cannot bootstrap without %s.\n' "$PYTHON_BIN" >&2
    exit 127
  fi
  exit 0
fi

if [[ ! -x "$CONSOLE_CLI" ]]; then
  if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    printf 'error: %s not found; install Python 3 or set PYTHON_BIN.\n' "$PYTHON_BIN" >&2
    exit 127
  fi
  "$PYTHON_BIN" -m venv "$VENV_DIR"
  . "$VENV_DIR/bin/activate"
  python -m pip install -e '.[dev]'
else
  . "$VENV_DIR/bin/activate"
fi

console-1701 init-config
exec console-1701 serve "${serve_args[@]}"
