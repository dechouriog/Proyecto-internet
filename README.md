# Sistema Distribuido de Monitoreo de Sensores IoT
**Internet: Arquitectura y Protocolos**

Sistema distribuido de monitoreo ambiental urbano en tiempo real, desplegado en AWS EC2. Recolecta datos de sensores IoT simulados (CO2, ruido, temperatura, PM2.5, humedad, UV), los procesa en un servidor central C++ y los visualiza a través de una interfaz gráfica de escritorio y un dashboard web accesible desde Internet.

---

## Arquitectura del Sistema

```
                        ┌─────────────────────────────┐
                        │       AWS Route 53           │
                        │  DNS: ec2-3-91-7-240.compute │
                        │       -1.amazonaws.com       │
                        └──────────────┬──────────────┘
                                       │
                        ┌──────────────▼──────────────┐
                        │        AWS EC2 (t2.micro)    │
                        │    Ubuntu 22.04 — Docker     │
                        │                              │
                        │  ┌─────────────────────┐     │
                        │  │  Servidor C++        │     │
                        │  │  puerto 5000         │     │
                        │  │  (Sockets Berkeley)  │     │
                        │  └──────────┬──────────┘     │
                        │             │ SQLite3         │
                        │  ┌──────────▼──────────┐     │
                        │  │  Login Service C++   │     │
                        │  │  puerto 6000         │     │
                        │  └─────────────────────┘     │
                        │  ┌─────────────────────┐     │
                        │  │  Web Server Python   │     │
                        │  │  puerto 8080 (HTTP)  │     │
                        │  └─────────────────────┘     │
                        └──────────────┬──────────────┘
                                       │ Internet
                    ┌──────────────────┴──────────────────┐
                    │                                       │
        ┌───────────▼───────────┐           ┌─────────────▼────────────┐
        │  Sensores IoT (Python) │           │  Operadores (Python/Tkinter│
        │  CO2, Ruido, Temp,     │           │  + Web Browser)           │
        │  PM2.5, Humedad, UV    │           │                           │
        └───────────────────────┘           └──────────────────────────┘
```

---

## Estructura del Proyecto

```
Proyecto-internet/
├── Dockerfile                          # Imagen Docker: compila C++ + inicializa DB
├── docker-compose.yml                  # Orquesta servidor C++, login y web
├── fix_tokens.sql                      # Script de corrección de tokens DB
│
├── server/
│   ├── server.cpp                      # Servidor principal (C++, Sockets Berkeley)
│   └── Makefile
│
├── Login_service/
│   ├── servicio_login.cpp              # Servicio de autenticación externo (C++)
│   ├── db_manager.cpp/h               # Gestión SQLite
│   ├── manejador_sesion.cpp/h         # Sesiones y tokens
│   ├── verificador_identidad.cpp/h    # Verificación de credenciales
│   ├── verificador_token.cpp/h        # Validación de tokens JWT-like
│   ├── operaciones_usuario.cpp/h      # Operaciones de usuario
│   └── Makefile
│
├── clients/
│   ├── sensor_simulator/              # Sensores IoT simulados (Python)
│   │   ├── sensor_base.py             # Clase base con lógica TCP
│   │   ├── sensor_co2.py
│   │   ├── sensor_ruido.py
│   │   ├── sensor_temperatura.py
│   │   ├── sensor_pm25.py
│   │   ├── sensor_humedad.py
│   │   ├── sensor_uv.py
│   │   └── run_sensors.py             # Lanzador de todos los sensores
│   └── operator_client/               # Cliente GUI operador (Python/Tkinter)
│       ├── operator_client.py         # Lógica de conexión TCP
│       └── operator_gui.py            # Interfaz gráfica
│
├── web/
│   ├── web_server.py                  # Servidor HTTP básico (Python)
│   └── index.html                     # Dashboard web
│
├── docs/database/
│   ├── schema.sql                     # Esquema de tablas
│   └── seed.sql                       # Datos iniciales
│
├── deployment/scripts/
│   ├── deploy_aws.sh                  # Despliegue completo en EC2
│   ├── reset_aws.sh                   # Reset de contenedores en EC2
│   ├── docker_entrypoint.sh           # Entrypoint del contenedor
│   └── start_server.sh                # Inicio manual sin Docker
│
└── logs/                              # Logs del servidor
```

---

## Tecnologías y Lenguajes

| Componente | Lenguaje | Tecnología |
|---|---|---|
| Servidor central | C++ | Sockets Berkeley (SOCK_STREAM/TCP) |
| Servicio de autenticación | C++ | Sockets TCP + SQLite3 |
| Sensores simulados | Python | socket stdlib |
| Cliente operador GUI | Python | Tkinter + socket stdlib |
| Servidor web HTTP | Python | socket stdlib (HTTP desde cero) |
| Base de datos | SQL | SQLite3 |
| Contenedor | - | Docker + docker-compose |
| Infraestructura | - | AWS EC2 Ubuntu 22.04 |

---

## Protocolo de Aplicación (Capa de Aplicación sobre TCP)

El protocolo es **basado en texto**, con campos separados por `|` para mensajes de sensores y autenticación, y por espacio para comandos de operadores. Cada mensaje termina con `\n`.

### Justificación del tipo de socket

Se utiliza **SOCK_STREAM (TCP)** en todos los componentes porque:
- Los datos de sensores deben llegar completos y en orden (no se puede perder una medición)
- El registro de sensores requiere confirmación del servidor
- El operador necesita respuestas fiables a sus consultas
- TCP elimina la necesidad de implementar retransmisión manual

### 1. Protocolo Sensor → Servidor (puerto 5000)

#### Registro de sensor
```
Cliente → Servidor:   REGISTER|<id>|<tipo>|<zona>|<unidad>|<token>
Servidor → Cliente:   OK REGISTERED
                      ERROR no_se_pudo_registrar_sensor
```
Ejemplo:
```
REGISTER|CO2-S01|co2|zona_centro|ppm|token_co2_001
OK REGISTERED
```

#### Envío de medición
```
Cliente → Servidor:   MEASURE|<sensor_id>|<valor>|<timestamp_unix>
Servidor → Cliente:   OK MEASURE_RECEIVED
                      OK SIMULATION_PAUSED
                      ERROR sensor_no_registrado
```
Ejemplo:
```
MEASURE|CO2-S01|534.7|1776894849
OK MEASURE_RECEIVED
```

#### Heartbeat (keep-alive)
```
Cliente → Servidor:   HEARTBEAT|<sensor_id>
Servidor → Cliente:   OK HEARTBEAT
```

### 2. Protocolo Operador → Servidor (puerto 5000)

```
Comando               Respuesta
─────────────────────────────────────────────────────────────────
GET_SENSORS         → SENSORS\n<id> | <tipo> | <zona> | <estado>\n...
GET_ALERTS          → ALERTS\n<id> | <sensor_id> | <tipo> | <nivel> | <msg> | <ts>\n...
GET_READINGS <id>   → READINGS\n<id> | <sensor_id> | <tipo> | <valor> | <ts>\n...
ACK_ALERT <id>      → OK alert_acknowledged
CLEAR_ALERTS        → OK cleared_alerts <n>
SYSTEM_STATUS       → SYSTEM_STATUS\n<campo> | <valor>\n...
PAUSE_SIMULATION    → OK simulation_paused
RESUME_SIMULATION   → OK simulation_resumed
```

Ejemplo de `GET_SENSORS`:
```
→ GET_SENSORS
← SENSORS
  CO2-S01 | co2 | zona_centro | activo
  HUM-S01 | humedad | zona_verde | activo
  PM2-S01 | pm25 | via_principal | activo
  RUI-S01 | ruido | zona_comercial | activo
  TMP-S01 | temperatura | parque_central | activo
  UVR-S01 | uv | plaza_publica | activo
```

### 3. Protocolo de Autenticación → Login Service (puerto 6000)

```
Operación   Formato
──────────────────────────────────────────────────────────────────────
LOGIN       Cliente → LOGIN|<usuario>|<password>
            OK:      OK|LOGIN|<user_id>|<token>|<refresh_token>|<msg>
            Error:   ERROR|LOGIN|<mensaje>

VALIDATE    Cliente → VALIDATE|<user_id>|<token>|<refresh_token>
            OK:      OK|VALIDATE|<nuevo_token>|<nuevo_refresh>|<msg>
            Error:   ERROR|VALIDATE|<mensaje>

LOGOUT      Cliente → LOGOUT|<user_id>|<token>|<refresh_token>
            OK:      OK|LOGOUT|session_closed
```

Ejemplo de login:
```
→ LOGIN|admin|admin123
← OK|LOGIN|1|eyJ0eXAiOiJ...|eyJ0eXAiOiJ...|login_exitoso
```

### 4. Protocolo HTTP — Servidor Web (puerto 8080)

Implementado desde cero con sockets Python. Soporta:

```
Método  Ruta              Respuesta
─────────────────────────────────────────────────────
GET     /                 200 — Dashboard HTML completo
GET     /index.html       200 — Dashboard HTML completo
GET     /api/status       200 — JSON con estado del sistema
GET     /api/sensors      200 — JSON con sensores y última lectura
GET     /api/alerts       200 — JSON con alertas recientes
*       cualquier otra    404 — Not Found
POST/PUT/... cualquiera   405 — Method Not Allowed
```

Ejemplo de respuesta `/api/status`:
```json
{
  "status": "online",
  "timestamp": "2026-04-23T02:21:34",
  "sensores_activos": 6,
  "total_sensores": 6,
  "total_alertas": 2,
  "alertas_criticas": 1
}
```

### Manejo de errores

- Si la resolución DNS falla, el cliente muestra advertencia y continúa
- El servidor no termina ante errores de red de un cliente
- Los sensores reconectan automáticamente con backoff exponencial (máx 30s)
- El servidor HTTP responde con códigos de estado apropiados en todos los casos

---

## Sensores y Umbrales de Alerta

| Sensor | Tipo | Unidad | Alerta MEDIUM | Alerta HIGH |
|---|---|---|---|---|
| CO2-S01 | co2 | ppm | > 700 ppm | > 1000 ppm |
| RUI-S01 | ruido | dB | > 65 dB | > 85 dB |
| TMP-S01 | temperatura | °C | > 32 °C | > 38 °C |
| PM2-S01 | pm25 | µg/m³ | > 35 µg/m³ | > 55 µg/m³ |
| HUM-S01 | humedad | % | < 15% o > 90% | — |
| UVR-S01 | uv | idx | > 7 | > 10 |

---

## Despliegue en AWS

### Infraestructura utilizada

| Recurso | Valor |
|---|---|
| Servicio | AWS EC2 |
| Tipo de instancia | t2.micro |
| AMI | Ubuntu 22.04 LTS |
| Región | us-east-1 (Norte de Virginia) |
| IP pública | Asignada dinámicamente (ver consola EC2) |
| DNS público | `ec2-<ip>.compute-1.amazonaws.com` |

### Security Groups configurados

| Puerto | Protocolo | Origen | Descripción |
|---|---|---|---|
| 22 | TCP | 0.0.0.0/0 | SSH administración |
| 5000 | TCP | 0.0.0.0/0 | Servidor IoT (sensores + operadores) |
| 6000 | TCP | 0.0.0.0/0 | Login Service |
| 8080 | TCP | 0.0.0.0/0 | Dashboard Web HTTP |

### Resolución de nombres DNS

El sistema utiliza el DNS público de EC2 proporcionado automáticamente por AWS:
```
ec2-<ip-publica>.compute-1.amazonaws.com
```

El cliente operador acepta hostname como argumento, eliminando IPs hardcodeadas:
```bash
python3 operator_gui.py --host ec2-3-91-7-240.compute-1.amazonaws.com --port 5000
```

Si la resolución DNS falla, el sistema muestra una advertencia pero continúa sin terminar abruptamente.

### Contenedor Docker en EC2

El servidor C++ se compila y ejecuta dentro de un contenedor Docker en la instancia EC2:

```
┌─────────────────────────────────────────┐
│  EC2 Ubuntu 22.04                        │
│  ┌───────────────────────────────────┐  │
│  │  Docker Container: monitoreo-     │  │
│  │  servidor (Ubuntu 22.04)          │  │
│  │  - Compila server.cpp con g++     │  │
│  │  - Compila login_service          │  │
│  │  - Inicializa database.db         │  │
│  │  - Ejecuta ./servidor 5000 ...    │  │
│  │  - Ejecuta ./login_service 6000   │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │  Docker Container: monitoreo-web  │  │
│  │  (python:3.11-slim)               │  │
│  │  - python3 web_server.py          │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

---

## Instrucciones de Despliegue

### 1. Requisitos previos en EC2

```bash
sudo apt-get update -y
sudo apt-get install -y docker-compose git
```

### 2. Clonar el repositorio

```bash
git clone https://github.com/dechouriog/Proyecto-internet.git
cd Proyecto-internet
```

### 3. Despliegue con Docker (recomendado)

```bash
bash deployment/scripts/deploy_aws.sh
```

Este script:
- Instala Docker si no está presente
- Construye la imagen (compila C++ dentro del contenedor)
- Inicializa la base de datos con schema + seed
- Levanta todos los servicios en background

### 4. Verificar que los servicios están activos

```bash
sudo docker-compose ps
```

Salida esperada:
```
Name                  Command         State    Ports
monitoreo-servidor   /app/entrypoint.sh  Up   0.0.0.0:5000->5000, 0.0.0.0:6000->6000
monitoreo-web        python3 web_server  Up   0.0.0.0:8080->8080
```

### 5. Conectar sensores (desde máquina local)

```bash
cd clients/sensor_simulator
python3 run_sensors.py --host <IP_PUBLICA_EC2> --port 5000
```

### 6. Abrir cliente operador GUI (desde máquina local)

```bash
cd clients/operator_client
python3 operator_gui.py --host <IP_PUBLICA_EC2> --port 5000
```

### 7. Acceder al dashboard web

```
http://<IP_PUBLICA_EC2>:8080
```

### Reset completo del despliegue

```bash
bash deployment/scripts/reset_aws.sh
```

---

## Ejecución del Servidor (sin Docker)

```bash
# Compilar
cd server && make

# Ejecutar
./servidor <puerto> <archivo_logs>

# Ejemplo
./servidor 5000 ../logs/servidor.log
```

---

## Credenciales del Sistema

| Usuario | Contraseña | Rol |
|---|---|---|
| admin | admin123 | admin |
| operador1 | op1234 | operator |

---

## Servicio de Autenticación

El servidor principal **no almacena usuarios**. Toda autenticación se delega al `login_service`, un proceso C++ independiente en el puerto 6000 con su propia base de datos (`users.db`). El servidor principal consulta este servicio externo para cada operación de login/validate/logout, cumpliendo con el requisito de no almacenar usuarios localmente.

---

## Logging del Servidor

Cada evento queda registrado en consola y en `logs/servidor.log` con el formato:

```
[YYYY-MM-DD HH:MM:SS] [IP:PUERTO] TIPO | RECIBIDO: <mensaje> | RESPUESTA: <respuesta>
```

Ejemplo:
```
[2026-04-23 02:21:34] [192.168.1.10:54321] SOLICITUD | RECIBIDO: MEASURE|CO2-S01|534.7|1776894849 | RESPUESTA: OK MEASURE_RECEIVED
[2026-04-23 02:21:34] [192.168.1.10:54321] SOLICITUD | RECIBIDO: GET_SENSORS | RESPUESTA: SENSORS
[2026-04-23 02:21:35] [192.168.1.10:54322] CONEXION  | RECIBIDO: nueva_conexion | RESPUESTA: cliente_conectado
[2026-04-23 02:21:36] [192.168.1.10:54322] DESCONEXION | RECIBIDO: cliente_desconectado | RESPUESTA: conexion_cerrada
```

---

## Enlace al Repositorio

[https://github.com/dechouriog/Proyecto-internet](https://github.com/dechouriog/Proyecto-internet)
