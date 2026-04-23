#!/usr/bin/env python3
import socket
import threading
import sqlite3
import json
import os
from datetime import datetime

# ── Configuración ───────────────────────────────────────────
HTTP_PORT = int(os.environ.get("HTTP_PORT", 8080))
DB_PATH = os.environ.get("DB_PATH", "/app/data/database.db")
SERVER_VER = "MonitoreoIoT/1.0"


# ── Helpers DB ──────────────────────────────────────────────
def query_db(sql, params=()):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.execute(sql, params)
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows
    except Exception as e:
        print(f"[DB ERROR] {e}")
        return []


def get_system_data():
    sensores = query_db("SELECT id, tipo, zona, estado FROM sensores ORDER BY id")

    alertas = query_db(
        "SELECT a.id, a.sensor_id, s.tipo, a.nivel, a.mensaje, a.timestamp "
        "FROM alertas a JOIN sensores s ON a.sensor_id=s.id "
        "ORDER BY a.id DESC LIMIT 20"
    )

    total_alertas_query = query_db("SELECT COUNT(*) as c FROM alertas")
    total_alertas = total_alertas_query[0]["c"] if total_alertas_query else 0

    # Última lectura por sensor desde tabla datos
    ultimas = query_db(
        "SELECT d.sensor_id, d.valor, d.timestamp, s.tipo "
        "FROM datos d JOIN sensores s ON d.sensor_id = s.id "
        "WHERE d.id IN (SELECT MAX(id) FROM datos GROUP BY sensor_id)"
    )
    ultimas_map = {r["sensor_id"]: r for r in ultimas}

    return sensores, alertas, total_alertas, ultimas_map


# ── HTTP Response ───────────────────────────────────────────
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


# ── Rutas ───────────────────────────────────────────────────
UNIDADES = {
    "co2": "ppm", "ruido": "dB", "temperatura": "°C",
    "pm25": "µg/m³", "humedad": "%", "uv": "idx"
}

def route_index():
    sensores, alertas, total_alertas, ultimas_map = get_system_data()

    activos = sum(1 for s in sensores if s["estado"] == "activo")
    criticas = sum(1 for a in alertas if a["nivel"] == "high")

    filas_sensores = ""
    for s in sensores:
        color = "#2ecc71" if s["estado"] == "activo" else "#e74c3c"
        u = ultimas_map.get(s["id"])
        if u:
            unidad = UNIDADES.get(u["tipo"], "")
            hora   = u["timestamp"].split(" ")[-1][:5] if u["timestamp"] else "--"
            ultima = f"<span style='color:#69f0ae'>{round(u['valor'],1)} {unidad}</span> <span style='color:#4caf50;font-size:.8em'>({hora})</span>"
        else:
            ultima = "<span style='color:#555'>Sin datos</span>"
        filas_sensores += (
            f"<tr><td>{s['id']}</td><td>{s['tipo']}</td>"
            f"<td>{s['zona']}</td>"
            f"<td style='color:{color};font-weight:bold'>{s['estado'].upper()}</td>"
            f"<td>{ultima}</td></tr>"
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

    return "<h1>Error: index.html no encontrado</h1>"


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
    ultimas  = query_db(
        "SELECT d.sensor_id, d.valor, d.timestamp FROM datos d "
        "WHERE d.id IN (SELECT MAX(id) FROM datos GROUP BY sensor_id)"
    )
    um = {r["sensor_id"]: r for r in ultimas}
    for s in sensores:
        u = um.get(s["id"])
        s["ultima_lectura"] = round(u["valor"], 2) if u else None
        s["ultima_hora"]    = u["timestamp"] if u else None
    return json.dumps(sensores, indent=2)


def route_api_alerts():
    alertas = query_db(
        "SELECT a.id, a.sensor_id, s.tipo, a.nivel, a.mensaje, a.timestamp "
        "FROM alertas a JOIN sensores s ON a.sensor_id=s.id "
        "ORDER BY a.id DESC LIMIT 50"
    )
    return json.dumps(alertas, indent=2)


# ── Dispatcher ──────────────────────────────────────────────
ROUTES = {
    "/": (route_index, "text/html; charset=utf-8"),
    "/index.html": (route_index, "text/html; charset=utf-8"),
    "/api/status": (route_api_status, "application/json"),
    "/api/sensors": (route_api_sensors, "application/json"),
    "/api/alerts": (route_api_alerts, "application/json"),
}


# ── Handler ─────────────────────────────────────────────────
def handle_client(conn, addr):
    try:
        raw = b""
        conn.settimeout(5)

        while b"\r\n\r\n" not in raw:
            chunk = conn.recv(1024)
            if not chunk:
                break
            raw += chunk

        if not raw:
            return

        request = raw.decode("utf-8", errors="replace")
        lines = request.split("\r\n")

        parts = lines[0].split(" ")
        if len(parts) < 2:
            conn.sendall(http_response(400, "<h1>400 Bad Request</h1>"))
            return

        method, path = parts[0], parts[1]
        path = path.split("?")[0]

        print(f"[HTTP] {addr[0]}:{addr[1]} {method} {path}")

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
        conn.close()


# ── Main ────────────────────────────────────────────────────
def main():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    srv.bind(("0.0.0.0", HTTP_PORT))
    srv.listen(20)

    print(f"[HTTP] Servidor web en http://0.0.0.0:{HTTP_PORT}")
    print(f"[HTTP] DB usada: {os.path.abspath(DB_PATH)}")

    while True:
        conn, addr = srv.accept()
        threading.Thread(
            target=handle_client,
            args=(conn, addr),
            daemon=True
        ).start()


if __name__ == "__main__":
    main()