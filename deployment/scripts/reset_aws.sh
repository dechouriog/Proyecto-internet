#!/bin/bash
# ============================================================
# reset_aws.sh — Resetea la DB en AWS y reinicia contenedores
# Ejecutar en EC2 cuando los sensores no envían datos
# ============================================================
echo ""
echo "============================================================"
echo "  RESET DEPLOYMENT — MONITOREO AMBIENTAL"
echo "============================================================"

# 1. Detener contenedores
echo "[1/4] Deteniendo contenedores..."
sudo docker compose down

# 2. Eliminar volumen con DB vieja (tokens incorrectos)
echo "[2/4] Eliminando volumen con DB antigua..."
sudo docker volume rm proyecto-internet-main_db_data 2>/dev/null || \
sudo docker volume rm $(sudo docker volume ls -q | grep db_data) 2>/dev/null || \
echo "      (volumen no encontrado, continuando)"

# 3. Reconstruir imagen (incluye seed.sql corregido)
echo "[3/4] Reconstruyendo imagen con fixes..."
sudo docker compose build --no-cache servidor

# 4. Levantar todo
echo "[4/4] Levantando servicios..."
sudo docker compose up -d

sleep 3
echo ""
echo "Estado de contenedores:"
sudo docker compose ps
echo ""
echo "Logs del servidor (últimas 20 líneas):"
sudo docker compose logs --tail=20 servidor
echo ""
echo "============================================================"
echo "  RESET COMPLETADO"
echo "  Conecta los sensores: python3 run_sensors.py --host <IP>"
echo "  Dashboard: http://<IP>:8080"
echo "============================================================"