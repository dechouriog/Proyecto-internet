#!/bin/bash
# start_server.sh - Inicia servidor principal y servicio de login
BASE_DIR="$(cd "$(dirname "$0")/../.." && pwd)"

echo "Iniciando Servicio de Login (puerto 6000)..."
cd "$BASE_DIR/Login_service"
./login_service &
LOGIN_PID=$!
echo "  PID Login: $LOGIN_PID"

sleep 1

echo "Iniciando Servidor Principal (puerto 5000)..."
cd "$BASE_DIR/server"
./servidor 5000 "$BASE_DIR/logs/servidor.log" &
SERVER_PID=$!
echo "  PID Servidor: $SERVER_PID"

echo ""
echo "Ambos servicios activos. Ctrl+C para detener."
trap "kill $LOGIN_PID $SERVER_PID 2>/dev/null; echo 'Servicios detenidos.'" INT
wait
