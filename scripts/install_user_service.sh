#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
PROJECT_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd -P)"
VENV_DIR="$PROJECT_DIR/.venv"
VENV_PYTHON="$VENV_DIR/bin/python"
CONSOLE_CLI="$VENV_DIR/bin/console-1701"
SERVICE_DIR="$HOME/.config/systemd/user"
CONFIG_PATH="$HOME/.config/console-1701/config.yml"
STATE_DIR="$HOME/.local/state/console-1701"

cd "$PROJECT_DIR"

python3 -m venv "$VENV_DIR"
if [[ ! -x "$VENV_PYTHON" ]]; then
  printf 'error: virtualenv Python missing after creation: %s\n' "$VENV_PYTHON" >&2
  exit 1
fi
"$VENV_PYTHON" -m pip install --upgrade pip
"$VENV_PYTHON" -m pip install -e '.[dev]'

if [[ ! -x "$CONSOLE_CLI" ]]; then
  printf 'error: console-1701 entry point missing after install: %s\n' "$CONSOLE_CLI" >&2
  exit 1
fi
if ! "$CONSOLE_CLI" --version >/dev/null 2>&1; then
  printf 'error: console-1701 entry point is not runnable: %s\n' "$CONSOLE_CLI" >&2
  exit 1
fi

mkdir -p "$(dirname "$CONFIG_PATH")" "$STATE_DIR" "$SERVICE_DIR"
"$CONSOLE_CLI" init-config --config "$CONFIG_PATH"

sed "s|__PROJECT_DIR__|$PROJECT_DIR|g" \
  systemd/console-1701.service > "$SERVICE_DIR/console-1701.service"
sed "s|__PROJECT_DIR__|$PROJECT_DIR|g" \
  systemd/console-1701-scan.service > "$SERVICE_DIR/console-1701-scan.service"
sed "s|__PROJECT_DIR__|$PROJECT_DIR|g" \
  systemd/console-1701-news-scan.service > "$SERVICE_DIR/console-1701-news-scan.service"
cp systemd/console-1701-scan.timer "$SERVICE_DIR/"
cp systemd/console-1701-news-scan.timer "$SERVICE_DIR/"

systemctl --user daemon-reload
systemctl --user enable --now console-1701.service
systemctl --user enable --now console-1701-scan.timer

"$CONSOLE_CLI" scan --config "$CONFIG_PATH"

echo "console-1701 is available at http://127.0.0.1:1701"
echo "console-1701-news-scan.timer was installed but left disabled."
