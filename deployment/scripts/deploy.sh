#!/bin/bash
# ============================================================
# deploy.sh - Despliegue en AWS EC2 Ubuntu
# Sistema de Monitoreo Ambiental Urbano
# ============================================================
set -e

echo "==================================================="
echo "  DESPLIEGUE - MONITOREO AMBIENTAL URBANO"
echo "==================================================="

# 1. Actualizar sistema
echo "[1/6] Actualizando paquetes del sistema..."
sudo apt-get update -y
sudo apt-get upgrade -y

# 2. Instalar dependencias
echo "[2/6] Instalando dependencias de compilacion..."
sudo apt-get install -y \
    build-essential \
    cmake \
    g++ \
    libsqlite3-dev \
    python3 \
    python3-pip \
    python3-tk \
    sqlite3

# 3. Compilar servidor principal
echo "[3/6] Compilando servidor principal..."
cd /home/ubuntu/proyecto-iot/server
make clean && make
echo "    -> servidor compilado"

# 4. Compilar servicio de login
echo "[4/6] Compilando servicio de login..."
cd /home/ubuntu/proyecto-iot/Login_service
make clean && make
echo "    -> login_service compilado"

# 5. Crear base de datos
echo "[5/6] Inicializando base de datos..."
cd /home/ubuntu/proyecto-iot
sqlite3 database.db < docs/database/schema.sql
sqlite3 database.db < docs/database/seed.sql
echo "    -> database.db creada"

# 6. Crear directorio de logs
echo "[6/6] Preparando directorio de logs..."
mkdir -p /home/ubuntu/proyecto-iot/logs
touch /home/ubuntu/proyecto-iot/logs/servidor.log
touch /home/ubuntu/proyecto-iot/logs/login.log

echo ""
echo "==================================================="
echo "  DESPLIEGUE COMPLETADO"
echo "==================================================="
echo ""
echo "  Para iniciar el servidor:"
echo "    cd server && ./servidor 5000 ../logs/servidor.log"
echo ""
echo "  Para iniciar el servicio de login:"
echo "    cd Login_service && ./login_service"
echo ""
echo "  Para iniciar los sensores (desde otro equipo):"
echo "    cd clients/sensor_simulator"
echo "    python3 run_sensors.py --host <IP_PUBLICA_EC2> --port 5000"
echo ""
echo "  Para abrir la GUI del operador:"
echo "    cd clients/operator_client"
echo "    python3 operator_gui.py"
echo "==================================================="
