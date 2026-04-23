# Sistema de Monitoreo Ambiental Urbano

Sistema distribuido de monitoreo en tiempo real para entornos urbanos. Recolecta datos de sensores ambientales (CO2, ruido, temperatura, PM2.5, humedad, UV), los procesa en un servidor central y los visualiza a través de un panel gráfico para operadores.

## Arquitectura

```
Sensores (Python)  -->  Servidor C++ (puerto 5000)  <--  GUI Operador (Python/Tkinter)
                               |
                         Login Service C++ (puerto 6000)
                               |
                          database.db (SQLite3)
```

## Estructura del Proyecto

```
proyecto-iot/
├── server/                     # Servidor principal (C++)
│   ├── server.cpp
│   ├── Makefile
│   └── CMakeLists.txt
├── Login_service/              # Servicio de autenticacion (C++)
│   ├── servicio_login.cpp
│   ├── manejador_sesion.cpp/h
│   ├── verificador_identidad.cpp/h
│   ├── verificador_token.cpp/h
│   ├── operaciones_usuario.cpp/h
│   ├── db_manager.cpp/h
│   └── Makefile
├── clients/
│   ├── sensor_simulator/       # Sensores ambientales (Python)
│   │   ├── sensor_base.py
│   │   ├── sensor_co2.py
│   │   ├── sensor_ruido.py
│   │   ├── sensor_temperatura.py
│   │   ├── sensor_pm25.py
│   │   ├── sensor_humedad.py
│   │   ├── sensor_uv.py
│   │   └── run_sensors.py
│   └── operator_client/        # Cliente GUI operador (Python/Tkinter)
│       ├── operator_client.py
│       ├── operator_gui.py
│       └── requirements.txt
├── docs/database/
│   ├── schema.sql
│   └── seed.sql
├── deployment/scripts/
│   ├── deploy.sh
│   └── start_server.sh
└── logs/
```

## Sensores Disponibles

| Sensor     | Tipo        | Unidad  | Alerta Media | Alerta Alta  |
|------------|-------------|---------|--------------|--------------|
| CO2-S01    | co2         | ppm     | > 700 ppm    | > 1000 ppm   |
| RUI-S01    | ruido       | dB      | > 65 dB      | > 85 dB      |
| TMP-S01    | temperatura | C       | > 32 C       | > 38 C       |
| PM2-S01    | pm25        | ug/m3   | > 35 ug/m3   | > 55 ug/m3   |
| HUM-S01    | humedad     | %       | < 15% o > 90%| -            |
| UVR-S01    | uv          | idx     | > 7          | > 10         |

## Protocolo de Comunicacion (TCP)

**Sensores → Servidor** (separado por `|`):
```
REGISTER|sensor_id|tipo|zona|unidad|token
MEASURE|sensor_id|valor|timestamp
HEARTBEAT|sensor_id
```

**Operador → Servidor** (separado por espacio):
```
GET_SENSORS
GET_ALERTS
GET_READINGS <sensor_id>
ACK_ALERT <alert_id>
CLEAR_ALERTS
SYSTEM_STATUS
PAUSE_SIMULATION
RESUME_SIMULATION
```

## Instalacion y Despliegue en AWS EC2

### Prerrequisitos en la instancia (Ubuntu 22.04)
```bash
sudo apt-get install -y build-essential libsqlite3-dev python3 python3-tk sqlite3
```

### Compilar
```bash
# Servidor principal
cd server && make

# Servicio de login
cd Login_service && make
```

### Crear base de datos
```bash
cd proyecto-iot
sqlite3 database.db < docs/database/schema.sql
sqlite3 database.db < docs/database/seed.sql
```

### Iniciar servicios
```bash
# Opcion 1: Script automatico
chmod +x deployment/scripts/start_server.sh
./deployment/scripts/start_server.sh

# Opcion 2: Manual
cd Login_service && ./login_service &
cd server       && ./servidor 5000 ../logs/servidor.log &
```

### Conectar sensores (desde local o EC2)
```bash
cd clients/sensor_simulator
python3 run_sensors.py --host <IP_PUBLICA_EC2> --port 5000
```

### Abrir GUI del operador
```bash
cd clients/operator_client
python3 operator_gui.py
```

## Configuracion Security Groups AWS

| Puerto | Protocolo | Descripcion                     |
|--------|-----------|---------------------------------|
| 22     | TCP       | SSH para administracion         |
| 5000   | TCP       | Servidor principal (sensores/GUI) |
| 6000   | TCP       | Servicio de autenticacion       |

## Credenciales por Defecto

| Usuario    | Contrasena | Rol       |
|------------|------------|-----------|
| admin      | admin123   | admin     |
| operador1  | op1234     | operator  |
