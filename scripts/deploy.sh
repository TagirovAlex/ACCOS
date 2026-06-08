#!/usr/bin/env bash
# Remote deploy script for ACCOS
# Uploaded and executed by deploy.py
set -e

OLD="/opt/accos"
NEW="/opt/accos_new"

echo '=== Stopping service ==='
systemctl stop accos

echo '=== Extracting ==='
cd /opt
rm -rf "$NEW"
tar xzf /tmp/accos.tar.gz
mv accos "$NEW"

echo '=== Preserving .venv, .env, logs ==='
[ -d "$OLD/.venv" ] && cp -a "$OLD/.venv" "$NEW/"
[ -f "$OLD/config/.env" ] && cp -a "$OLD/config/.env" "$NEW/config/"
[ -d "$OLD/logs" ] && cp -a "$OLD/logs" "$NEW/"

rm -rf "$OLD" && mv "$NEW" "$OLD"
rm -f /tmp/accos.tar.gz

echo '=== Python deps ==='
cd "$OLD" && .venv/bin/pip install -q -r backend/requirements.txt

echo '=== Building admin ==='
cd "$OLD/admin" && npm install --silent && npm run build

echo '=== Building frontend ==='
cd "$OLD/frontend" && npm install --silent && npm run build

echo '=== Migrations ==='
cd "$OLD" && .venv/bin/alembic -c config/alembic.ini upgrade head 2>&1

echo '=== Restarting ==='
systemctl daemon-reload || true
for i in 1 2 3; do
  systemctl start accos && { sleep 3; break; }
  echo "Retry $i..."
  sleep 2
done
systemctl status accos --no-pager -l | head -20

echo '=== Done ==='
