#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
PROJECT_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd -P)"
SERVICE_DIR="$HOME/.config/systemd/user"
CONFIG_PATH="$HOME/.config/console-1701/config.yml"
STATE_DIR="$HOME/.local/state/console-1701"

cd "$PROJECT_DIR"

python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'

mkdir -p "$(dirname "$CONFIG_PATH")" "$STATE_DIR" "$SERVICE_DIR"
console-1701 init-config --config "$CONFIG_PATH"

sed "s|__PROJECT_DIR__|$PROJECT_DIR|g" \
  systemd/console-1701.service > "$SERVICE_DIR/console-1701.service"
sed "s|__PROJECT_DIR__|$PROJECT_DIR|g" \
  systemd/console-1701-scan.service > "$SERVICE_DIR/console-1701-scan.service"
cp systemd/console-1701-scan.timer "$SERVICE_DIR/"

systemctl --user daemon-reload
systemctl --user enable --now console-1701.service
systemctl --user enable --now console-1701-scan.timer

console-1701 scan --config "$CONFIG_PATH"

echo "console-1701 is available at http://127.0.0.1:1701"
