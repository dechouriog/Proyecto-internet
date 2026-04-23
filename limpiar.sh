#!/bin/bash
# ============================================================
# limpiar.sh — Resetea el proyecto a estado limpio
# ============================================================
BASE="$(cd "$(dirname "$0")" && pwd)"
cd "$BASE"

echo ""
echo "=================================================="
echo "  LIMPIEZA TOTAL — MONITOREO AMBIENTAL"
echo "=================================================="

# Binarios compilados
echo ""
echo "[1/4] Eliminando binarios..."
rm -f server/servidor Login_service/login_service
echo "      -> OK"

# Base de datos
echo "[2/4] Eliminando base de datos..."
rm -f database.db Login_service/users.db Login_service/log_sesiones
echo "      -> OK"

# Logs
echo "[3/4] Limpiando logs..."
rm -f logs/*.log
touch logs/.gitkeep
echo "      -> OK"

# Archivos temporales Python
echo "[4/4] Eliminando cachés Python..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete 2>/dev/null
echo "      -> OK"

echo ""
echo "=================================================="
echo "  LISTO. Proyecto en estado limpio."
echo "=================================================="
echo ""