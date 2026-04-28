#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$HOME/projects/console-1706"
SERVICE_DIR="$HOME/.config/systemd/user"
CONFIG_PATH="$HOME/.config/console-1706/config.yml"
STATE_DIR="$HOME/.local/state/console-1706"

if [[ "$(pwd -P)" != "$PROJECT_DIR" ]]; then
  echo "Warning: expected to run from $PROJECT_DIR, currently in $(pwd -P)." >&2
fi

python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'

mkdir -p "$(dirname "$CONFIG_PATH")" "$STATE_DIR" "$SERVICE_DIR"
console-1706 init-config --config "$CONFIG_PATH"

cp systemd/console-1706.service "$SERVICE_DIR/"
cp systemd/console-1706-scan.service "$SERVICE_DIR/"
cp systemd/console-1706-scan.timer "$SERVICE_DIR/"

systemctl --user daemon-reload
systemctl --user enable --now console-1706.service
systemctl --user enable --now console-1706-scan.timer

console-1706 scan --config "$CONFIG_PATH"

echo "console-1706 is available at http://127.0.0.1:1706"
