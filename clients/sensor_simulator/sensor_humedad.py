#!/usr/bin/env python3
"""Sensor Humedad Relativa - Monitoreo Ambiental Urbano | Rango: 0-100%"""
import random, sys
from sensor_base import SensorBase


class SensorHumedad(SensorBase):
    def __init__(
        self,
        sensor_id="HUM-S01",
        zona="zona_verde",
        unidad="%",
        token="token_hum_001",
        host="localhost",
        puerto=5000,
    ):
        super().__init__(sensor_id, "humedad", zona, unidad, token, host, puerto)
        self.valor_actual = 62.0

    def generar_medicion(self):
        if random.random() < 0.94:
            self.valor_actual += random.gauss(0, 0.3)
        else:
            salto = random.choice([-8, -5, 5, 10])
            self.valor_actual += salto
            self.logger.warning(f"Cambio brusco humedad: {salto:+}%")
        self.valor_actual = max(0, min(100, self.valor_actual))
        return round(self.valor_actual, 1)


if __name__ == "__main__":
    host = sys.argv[1] if len(sys.argv) > 1 else "localhost"
    puerto = int(sys.argv[2]) if len(sys.argv) > 2 else 5000
    SensorHumedad(host=host, puerto=puerto).iniciar()
