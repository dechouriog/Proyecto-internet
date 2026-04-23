#!/bin/bash
# ============================================================
# docker_entrypoint.sh — Arranca login_service + servidor
# ============================================================
set -e
BASE="/app"
LOG_DIR="$BASE/logs"
mkdir -p "$LOG_DIR"

echo "[ENTRYPOINT] Iniciando Login Service (puerto 6000)..."
cd "$BASE/Login_service"
./login_service 6000 "$LOG_DIR/login.log" &
LOGIN_PID=$!
sleep 1

if ! kill -0 $LOGIN_PID 2>/dev/null; then
    echo "[ENTRYPOINT] ERROR: login_service no arrancó"
    exit 1
fi
echo "[ENTRYPOINT] login_service PID=$LOGIN_PID OK"

echo "[ENTRYPOINT] Iniciando Servidor Principal (puerto 5000)..."
cd "$BASE/server"
exec ./servidor 5000 "$LOG_DIR/servidor.log"