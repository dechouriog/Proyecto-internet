#!/bin/bash
# ============================================================
# reset_aws.sh — Compatible con docker-compose v1 y v2
# ============================================================
set -e

# Detectar versión de docker compose
if docker compose version &>/dev/null 2>&1; then
    DC="docker compose"
elif command -v docker-compose &>/dev/null; then
    DC="docker-compose"
else
    echo "ERROR: No se encontró docker-compose. Instalando..."
    sudo apt-get install -y docker-compose
    DC="docker-compose"
fi

echo ""
echo "============================================================"
echo "  RESET DEPLOYMENT — MONITOREO AMBIENTAL"
echo "  Usando: $DC"
echo "============================================================"

# 1. Detener contenedores
echo "[1/4] Deteniendo contenedores..."
sudo $DC down 2>/dev/null || true

# 2. Eliminar volumen con DB vieja
echo "[2/4] Eliminando volumen con DB antigua..."
sudo docker volume rm proyecto-internet-main_db_data 2>/dev/null && echo "      -> volumen eliminado" || \
sudo docker volume rm $(sudo docker volume ls -q 2>/dev/null | grep db_data | head -1) 2>/dev/null && echo "      -> volumen eliminado" || \
echo "      -> (volumen no encontrado, continuando)"

# 3. Reconstruir imagen
echo "[3/4] Reconstruyendo imagen con fixes..."
sudo $DC build --no-cache servidor

# 4. Levantar todo
echo "[4/4] Levantando servicios..."
sudo $DC up -d

sleep 3
echo ""
echo "Estado de contenedores:"
sudo $DC ps
echo ""
echo "Logs del servidor (últimas 20 líneas):"
sudo $DC logs --tail=20 servidor 2>/dev/null || sudo $DC logs servidor 2>/dev/null | tail -20
echo ""
echo "============================================================"
echo "  RESET COMPLETADO"
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "<IP_EC2>")
echo "  Conecta sensores: python3 run_sensors.py --host $PUBLIC_IP --port 5000"
echo "  Dashboard:        http://$PUBLIC_IP:8080"
echo "============================================================"