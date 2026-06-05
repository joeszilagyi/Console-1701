#!/usr/bin/env bash
set -euo pipefail

# Start a local development server from any working directory.
# Side effects: creates/updates the repo-local .venv and default console-1701 config as needed.
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
PROJECT_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd -P)"
VENV_DIR="$PROJECT_DIR/.venv"
VENV_PYTHON="$VENV_DIR/bin/python"
CONSOLE_CLI="$VENV_DIR/bin/console-1701"
PYTHON_BIN="${PYTHON_BIN:-python3}"

usage() {
  cat <<'EOF'
Usage: scripts/dev_server.sh [--check] [--help] [-- SERVE_ARGS...]

Bootstrap the repo-local .venv if needed, initialize the default config, then
run `console-1701 serve`. The application itself enforces 127.0.0.1 binding.

Options:
  --check  Show resolved paths and bootstrap prerequisites without creating .venv or serving.
  --help   Show this help.

Arguments after -- are forwarded to `console-1701 serve`.
EOF
}

ensure_venv_python() {
  if [[ -x "$VENV_PYTHON" ]]; then
    return 0
  fi

  if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    printf 'error: %s not found; install Python 3 or set PYTHON_BIN.\n' "$PYTHON_BIN" >&2
    exit 127
  fi

  printf 'Creating virtualenv: %s\n' "$VENV_DIR" >&2
  "$PYTHON_BIN" -m venv "$VENV_DIR"
  if [[ ! -x "$VENV_PYTHON" ]]; then
    printf 'error: virtualenv Python missing after creation: %s\n' "$VENV_PYTHON" >&2
    exit 1
  fi
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
  check_failed=false
  printf 'Project: %s\n' "$PROJECT_DIR"
  python_path="$(command -v "$PYTHON_BIN" || true)"
  if [[ -n "$python_path" ]]; then
    printf 'Python: %s\n' "$python_path"
  else
    printf 'Python: missing (%s)\n' "$PYTHON_BIN"
  fi
  if [[ -x "$VENV_PYTHON" ]]; then
    printf 'Venv Python: %s\n' "$VENV_PYTHON"
  else
    printf 'Venv Python: missing (%s)\n' "$VENV_PYTHON"
  fi
  if [[ -x "$CONSOLE_CLI" ]]; then
    if "$CONSOLE_CLI" --version >/dev/null 2>&1; then
      printf 'CLI: %s (runnable)\n' "$CONSOLE_CLI"
    else
      printf 'CLI: present but not runnable (%s)\n' "$CONSOLE_CLI"
      check_failed=true
    fi
  else
    printf 'CLI: missing (%s)\n' "$CONSOLE_CLI"
  fi
  if [[ "$check_failed" == true ]]; then
    printf 'error: existing console-1701 CLI is not runnable; reinstall the venv.\n' >&2
    exit 1
  fi
  if [[ ! -x "$CONSOLE_CLI" && -z "$python_path" ]]; then
    printf 'error: cannot bootstrap without %s.\n' "$PYTHON_BIN" >&2
    exit 127
  fi
  exit 0
fi

if [[ ! -x "$CONSOLE_CLI" ]]; then
  ensure_venv_python
  printf 'Installing console-1701 with development dependencies.\n' >&2
  "$VENV_PYTHON" -m pip install -e '.[dev]'
fi

if [[ ! -x "$CONSOLE_CLI" ]]; then
  printf 'error: console-1701 entry point missing after install: %s\n' "$CONSOLE_CLI" >&2
  exit 1
fi

if ! "$CONSOLE_CLI" --version >/dev/null 2>&1; then
  printf 'error: console-1701 entry point is not runnable: %s\n' "$CONSOLE_CLI" >&2
  exit 1
fi

printf 'Initializing default config if missing.\n' >&2
"$CONSOLE_CLI" init-config
printf 'Starting console-1701 development server on localhost.\n' >&2
exec "$CONSOLE_CLI" serve "${serve_args[@]}"
