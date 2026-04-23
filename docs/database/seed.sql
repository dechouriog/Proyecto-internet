-- ============================================================
-- DATOS INICIALES - MONITOREO AMBIENTAL URBANO
-- ============================================================

INSERT INTO usuarios (username, password, role) VALUES
('admin',      'admin123', 'admin'),
('operador1',  'op1234',   'operator');

INSERT INTO sensores (id, tipo, zona, token, estado) VALUES
('CO2-S01', 'co2',         'zona_centro',    'token_defecto',  'activo'),
('RUI-S01', 'ruido',       'zona_comercial', 'token_defecto',  'activo'),
('TMP-S01', 'temperatura', 'parque_central', 'token_defecto',  'activo'),
('PM2-S01', 'pm25',        'via_principal',  'token_defecto',  'activo'),
('HUM-S01', 'humedad',     'zona_verde',     'token_defecto',  'activo'),
('UVR-S01', 'uv',          'plaza_publica',  'token_defecto',  'activo');

INSERT INTO datos (sensor_id, valor) VALUES
('CO2-S01', 450.0),
('RUI-S01',  58.3),
('TMP-S01',  26.1),
('PM2-S01',  22.4),
('HUM-S01',  64.5),
('UVR-S01',   4.2);

INSERT INTO alertas (sensor_id, nivel, mensaje) VALUES
('CO2-S01', 'medium', 'Nivel de CO2 elevado en zona_centro'),
('RUI-S01', 'high',   'Contaminacion acustica grave detectada en zona_comercial');