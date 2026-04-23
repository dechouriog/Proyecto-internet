#!/usr/bin/env python3
"""
web_server.py — Servidor HTTP básico para el Sistema de Monitoreo Ambiental Urbano
Requisito: interpretar cabeceras HTTP, manejar GET, devolver códigos de estado.
Puerto: 80 (o 8080 si no hay permisos de root)
"""
import socket
import threading
import sqlite3
import json
import os
from datetime import datetime

# ── Configuración ─────────────────────────────────────────────────────────────
HTTP_PORT = int(os.environ.get("HTTP_PORT", 8080))
DB_PATH = os.environ.get("DB_PATH", "../database.db")
SERVER_VER = "MonitoreoIoT/1.0"


# ── Helpers DB ────────────────────────────────────────────────────────────────
def query_db(sql, params=()):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.execute(sql, params)
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows
    except Exception as e:
        return []


def get_system_data():
    sensores = query_db("SELECT id, tipo, zona, estado FROM sensores ORDER BY id")
    alertas = query_db(
        "SELECT a.id, a.sensor_id, s.tipo, a.nivel, a.mensaje, a.timestamp "
        "FROM alertas a JOIN sensores s ON a.sensor_id=s.id ORDER BY a.id DESC LIMIT 20"
    )
    total_alertas = (
        query_db("SELECT COUNT(*) as c FROM alertas")[0]["c"]
        if query_db("SELECT COUNT(*) as c FROM alertas")
        else 0
    )
    return sensores, alertas, total_alertas


# ── Generador de respuestas HTTP ──────────────────────────────────────────────
def http_response(status_code, body, content_type="text/html; charset=utf-8"):
    reasons = {
        200: "OK",
        400: "Bad Request",
        404: "Not Found",
        405: "Method Not Allowed",
    }
    reason = reasons.get(status_code, "Unknown")
    headers = (
        f"HTTP/1.1 {status_code} {reason}\r\n"
        f"Content-Type: {content_type}\r\n"
        f"Content-Length: {len(body.encode('utf-8'))}\r\n"
        f"Server: {SERVER_VER}\r\n"
        f"Connection: close\r\n"
        f"\r\n"
    )
    return (headers + body).encode("utf-8")


# ── Rutas ─────────────────────────────────────────────────────────────────────
def route_index():
    sensores, alertas, total_alertas = get_system_data()
    activos = sum(1 for s in sensores if s["estado"] == "activo")
    criticas = sum(1 for a in alertas if a["nivel"] == "high")

    filas_sensores = ""
    for s in sensores:
        color = "#2ecc71" if s["estado"] == "activo" else "#e74c3c"
        filas_sensores += (
            f"<tr><td>{s['id']}</td><td>{s['tipo']}</td>"
            f"<td>{s['zona']}</td>"
            f"<td style='color:{color};font-weight:bold'>{s['estado'].upper()}</td></tr>"
        )

    filas_alertas = ""
    for a in alertas[:10]:
        color = (
            "#e74c3c"
            if a["nivel"] == "high"
            else ("#f39c12" if a["nivel"] == "medium" else "#27ae60")
        )
        filas_alertas += (
            f"<tr style='color:{color}'><td>{a['id']}</td><td>{a['sensor_id']}</td>"
            f"<td>{a['tipo']}</td><td>{a['nivel'].upper()}</td>"
            f"<td>{a['mensaje']}</td><td>{a['timestamp']}</td></tr>"
        )

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    html_path = os.path.join(os.path.dirname(__file__), "index.html")
    if os.path.exists(html_path):
        with open(html_path, encoding="utf-8") as f:
            template = f.read()
        return (
            template.replace("{{ACTIVOS}}", str(activos))
            .replace("{{TOTAL}}", str(len(sensores)))
            .replace("{{ALERTAS_TOTAL}}", str(total_alertas))
            .replace("{{CRITICAS}}", str(criticas))
            .replace("{{FILAS_SENSORES}}", filas_sensores)
            .replace("{{FILAS_ALERTAS}}", filas_alertas)
            .replace("{{TIMESTAMP}}", now)
        )
    return f"<h1>Error: index.html no encontrado</h1>"


def route_api_status():
    sensores, alertas, total_alertas = get_system_data()
    data = {
        "status": "online",
        "timestamp": datetime.now().isoformat(),
        "sensores_activos": sum(1 for s in sensores if s["estado"] == "activo"),
        "total_sensores": len(sensores),
        "total_alertas": total_alertas,
        "alertas_criticas": sum(1 for a in alertas if a["nivel"] == "high"),
    }
    return json.dumps(data, indent=2)


def route_api_sensors():
    sensores = query_db("SELECT id, tipo, zona, estado FROM sensores ORDER BY id")
    return json.dumps(sensores, indent=2)


def route_api_alerts():
    alertas = query_db(
        "SELECT a.id, a.sensor_id, s.tipo, a.nivel, a.mensaje, a.timestamp "
        "FROM alertas a JOIN sensores s ON a.sensor_id=s.id ORDER BY a.id DESC LIMIT 50"
    )
    return json.dumps(alertas, indent=2)


# ── Dispatcher ────────────────────────────────────────────────────────────────
ROUTES = {
    "/": (route_index, "text/html; charset=utf-8"),
    "/index.html": (route_index, "text/html; charset=utf-8"),
    "/api/status": (route_api_status, "application/json"),
    "/api/sensors": (route_api_sensors, "application/json"),
    "/api/alerts": (route_api_alerts, "application/json"),
}


# ── Handler de conexión ───────────────────────────────────────────────────────
def handle_client(conn, addr):
    try:
        raw = b""
        conn.settimeout(5)
        try:
            while b"\r\n\r\n" not in raw:
                chunk = conn.recv(1024)
                if not chunk:
                    break
                raw += chunk
        except:
            pass

        if not raw:
            return

        request = raw.decode("utf-8", errors="replace")
        lines = request.split("\r\n")
        if not lines:
            conn.sendall(http_response(400, "<h1>400 Bad Request</h1>"))
            return

        # Parsear request line: "GET /path HTTP/1.1"
        parts = lines[0].split(" ")
        if len(parts) < 2:
            conn.sendall(http_response(400, "<h1>400 Bad Request</h1>"))
            return

        method, path = parts[0], parts[1]
        # Ignorar query string
        path = path.split("?")[0]

        print(
            f"[{datetime.now().strftime('%H:%M:%S')}] {addr[0]}:{addr[1]} {method} {path}"
        )

        if method != "GET":
            conn.sendall(http_response(405, "<h1>405 Method Not Allowed</h1>"))
            return

        if path in ROUTES:
            fn, ctype = ROUTES[path]
            body = fn()
            conn.sendall(http_response(200, body, ctype))
        else:
            conn.sendall(http_response(404, "<h1>404 Not Found</h1>"))

    except Exception as e:
        print(f"[HTTP ERROR] {addr}: {e}")
    finally:
        try:
            conn.close()
        except:
            pass


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("0.0.0.0", HTTP_PORT))
    srv.listen(20)
    print(f"[HTTP] Servidor web en http://0.0.0.0:{HTTP_PORT}")
    print(f"[HTTP] DB: {os.path.abspath(DB_PATH)}")
    while True:
        try:
            conn, addr = srv.accept()
            threading.Thread(
                target=handle_client, args=(conn, addr), daemon=True
            ).start()
        except KeyboardInterrupt:
            print("\n[HTTP] Detenido.")
            break
        except Exception as e:
            print(f"[HTTP ERROR] {e}")
    srv.close()


if __name__ == "__main__":
    main()
