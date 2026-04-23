#!/bin/bash
# ============================================================
# docker_entrypoint.sh — Arranca DB + login_service + servidor
# ============================================================
set -e

BASE="/app"
LOG_DIR="$BASE/logs"
DB_DIR="$BASE/data"
DB_PATH="$DB_DIR/database.db"

mkdir -p "$LOG_DIR"
mkdir -p "$DB_DIR"

echo "[ENTRYPOINT] Verificando base de datos..."

if [ ! -f "$DB_PATH" ]; then
    echo "[ENTRYPOINT] Creando base de datos..."

    sqlite3 "$DB_PATH" < "$BASE/docs/database/schema.sql"
    sqlite3 "$DB_PATH" < "$BASE/docs/database/seed.sql"

    echo "[ENTRYPOINT] DB inicializada"
else
    echo "[ENTRYPOINT] DB ya existe, no se toca"
fi

# ── Login Service ───────────────────────────────────────────
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

# ── Servidor principal ──────────────────────────────────────
echo "[ENTRYPOINT] Iniciando Servidor Principal (puerto 5000)..."
cd "$BASE/server"
exec ./servidor 5000 "$LOG_DIR/servidor.log"