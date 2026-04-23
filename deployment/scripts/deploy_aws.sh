#!/bin/bash
# ============================================================
# deploy_aws.sh — Despliegue completo en EC2 Ubuntu 22.04
# Uso: bash deployment/scripts/deploy_aws.sh
# ============================================================
set -e

echo ""
echo "============================================================"
echo "  DESPLIEGUE AWS EC2 — MONITOREO AMBIENTAL URBANO"
echo "============================================================"

# ── 1. Actualizar sistema ─────────────────────────────────────
echo ""
echo "[1/5] Actualizando sistema..."
sudo apt-get update -y -q
sudo apt-get upgrade -y -q

# ── 2. Instalar Docker ────────────────────────────────────────
echo ""
echo "[2/5] Instalando Docker..."
if ! command -v docker &>/dev/null; then
    sudo apt-get install -y -q ca-certificates curl gnupg
    sudo install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
        sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
        https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | \
        sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update -y -q
    sudo apt-get install -y -q docker-ce docker-ce-cli containerd.io docker-compose-plugin
    sudo usermod -aG docker $USER
    echo "      -> Docker instalado"
else
    echo "      -> Docker ya instalado: $(docker --version)"
fi

# ── 3. Instalar dependencias extra (para clientes externos) ──
echo ""
echo "[3/5] Instalando Python y dependencias..."
sudo apt-get install -y -q python3 python3-pip sqlite3
echo "      -> OK"

# ── 4. Construir y levantar contenedores ─────────────────────
echo ""
echo "[4/5] Construyendo y levantando contenedores..."
cd "$(dirname "$0")/../.."   # ir a raíz del proyecto

# Crear DB vacía si no existe (docker-compose la monta como volumen)
if [ ! -f database.db ]; then
    sqlite3 database.db < docs/database/schema.sql
    sqlite3 database.db < docs/database/seed.sql
    echo "      -> database.db creada"
fi

mkdir -p logs

sudo docker compose up -d --build
echo "      -> Contenedores levantados"

# ── 5. Verificar estado ───────────────────────────────────────
echo ""
echo "[5/5] Verificando servicios..."
sleep 3
sudo docker compose ps

echo ""
echo "============================================================"
echo "  DESPLIEGUE COMPLETADO"
echo "============================================================"

# Obtener IP pública de la instancia
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "ver consola AWS")

echo ""
echo "  IP pública EC2 : $PUBLIC_IP"
echo ""
echo "  Servicios disponibles:"
echo "    Servidor IoT   → $PUBLIC_IP:5000  (sensores/operadores)"
echo "    Login Service  → $PUBLIC_IP:6000"
echo "    Dashboard Web  → http://$PUBLIC_IP:8080"
echo ""
echo "  Si configuraste Route 53:"
echo "    Dashboard Web  → http://iot-monitoring.example.com:8080"
echo ""
echo "  Conectar sensores desde otra máquina:"
echo "    python3 run_sensors.py --host $PUBLIC_IP --port 5000"
echo ""
echo "  Ver logs en tiempo real:"
echo "    sudo docker compose logs -f servidor"
echo "============================================================"