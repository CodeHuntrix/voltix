#!/usr/bin/env bash
# Voltix edge install on Raspberry Pi (Debian/Ubuntu)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
python3 -m venv "$ROOT/.venv"
source "$ROOT/.venv/bin/activate"
pip install -U pip
pip install -r "$ROOT/requirements.txt"
mkdir -p /var/lib/voltix-edge
cat >/etc/systemd/system/voltix-edge.service <<EOF
[Unit]
Description=Voltix Edge Gateway
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=$ROOT
Environment=CLOUD_URL=${CLOUD_URL:-http://127.0.0.1:8000}
Environment=EDGE_INGEST_API_KEY=${EDGE_INGEST_API_KEY:-voltix-edge-dev-key}
Environment=MQTT_HOST=${MQTT_HOST:-127.0.0.1}
Environment=EDGE_BUFFER_PATH=/var/lib/voltix-edge/buffer.sqlite
ExecStart=$ROOT/.venv/bin/python $ROOT/gateway.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable voltix-edge
systemctl restart voltix-edge
echo "Voltix edge installed. Configure CLOUD_URL / SITE_ID / MQTT_HOST then restart."
