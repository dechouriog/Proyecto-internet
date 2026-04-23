#!/usr/bin/env python3
"""Sensor Temperatura Ambiental - Monitoreo Urbano | Rango: 5-45 C"""
import random, sys
from sensor_base import SensorBase


class SensorTemperatura(SensorBase):
    def __init__(
        self,
        sensor_id="TMP-S01",
        zona="parque_central",
        unidad="C",
        token="token_tmp_001",
        host="localhost",
        puerto=5000,
    ):
        super().__init__(sensor_id, "temperatura", zona, unidad, token, host, puerto)
        self.valor_actual = 24.0

    def generar_medicion(self):
        if random.random() < 0.91:
            self.valor_actual += random.gauss(0, 0.4)
        else:
            salto = random.choice([-2, -1, 1, 2, 3])
            self.valor_actual += salto
            self.logger.warning(f"Cambio brusco temperatura: {salto:+}C")
        self.valor_actual = max(5, min(45, self.valor_actual))
        return round(self.valor_actual, 1)


if __name__ == "__main__":
    host = sys.argv[1] if len(sys.argv) > 1 else "localhost"
    puerto = int(sys.argv[2]) if len(sys.argv) > 2 else 5000
    SensorTemperatura(host=host, puerto=puerto).iniciar()
