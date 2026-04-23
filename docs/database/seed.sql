-- ============================================================
-- DATOS INICIALES - MONITOREO AMBIENTAL URBANO
-- ============================================================

-- Usuarios
INSERT OR IGNORE INTO usuarios (username, password, role) VALUES
('admin',      'admin123', 'admin'),
('operador1',  'op1234',   'operator');

-- Sensores (tokens únicos)
INSERT OR IGNORE INTO sensores (id, tipo, zona, token, estado) VALUES
('CO2-S01', 'co2',         'zona_centro',    'tk_co2_001',   'activo'),
('RUI-S01', 'ruido',       'zona_comercial', 'tk_ruido_001', 'activo'),
('TMP-S01', 'temperatura', 'parque_central', 'tk_tmp_001',   'activo'),
('PM2-S01', 'pm25',        'via_principal',  'tk_pm25_001',  'activo'),
('HUM-S01', 'humedad',     'zona_verde',     'tk_hum_001',   'activo'),
('UVR-S01', 'uv',          'plaza_publica',  'tk_uv_001',    'activo');

-- Datos iniciales
INSERT OR IGNORE INTO datos (sensor_id, valor) VALUES
('CO2-S01', 450.0),
('RUI-S01',  58.3),
('TMP-S01',  26.1),
('PM2-S01',  22.4),
('HUM-S01',  64.5),
('UVR-S01',   4.2);

-- Alertas iniciales
INSERT OR IGNORE INTO alertas (sensor_id, nivel, mensaje) VALUES
('CO2-S01', 'medium', 'Nivel de CO2 elevado en zona_centro'),
('RUI-S01', 'high',   'Contaminacion acustica grave detectada en zona_comercial');