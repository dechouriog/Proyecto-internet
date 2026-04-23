-- ============================================================
-- ESQUEMA DE BASE DE DATOS - MONITOREO AMBIENTAL URBANO
-- ============================================================

CREATE TABLE IF NOT EXISTS usuarios (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    role     TEXT NOT NULL CHECK(role IN ('admin', 'operator'))
);

CREATE TABLE IF NOT EXISTS sensores (
    id     TEXT PRIMARY KEY,
    tipo   TEXT NOT NULL,
    zona   TEXT NOT NULL,
    token  TEXT NOT NULL UNIQUE,
    estado TEXT NOT NULL CHECK(estado IN ('activo', 'inactivo', 'mantenimiento'))
);

CREATE TABLE IF NOT EXISTS datos (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    sensor_id TEXT NOT NULL,
    valor     REAL NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sensor_id) REFERENCES sensores(id)
);

CREATE TABLE IF NOT EXISTS alertas (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    sensor_id TEXT NOT NULL,
    nivel     TEXT NOT NULL CHECK(nivel IN ('low', 'medium', 'high', 'critical')),
    mensaje   TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sensor_id) REFERENCES sensores(id)
);

CREATE TABLE IF NOT EXISTS logs (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    origen    TEXT NOT NULL,
    accion    TEXT NOT NULL,
    detalle   TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
